# -*- coding: utf-8 -*-
from bda.cache import ICacheManager
from bda.cache.interfaces import INullCacheProvider
from node.ext.ldap.cache import nullcacheProviderFactory
from node.ext.ldap.interfaces import ICacheProviderFactory
from node.ext.ldap.properties import LDAPProps
from zope.component import queryUtility
import hashlib
import ldap
import logging
import six


logger = logging.getLogger('node.ext.ldap')


def testLDAPConnectivity(server=None, port=None, props=None):
    """Function to test the availability of the LDAP Server.

    :param server: Server IP or name
    :param port: LDAP port
    :param props: LDAPProps object. If given, server and port are ignored.
    :return object: Either string 'success' if connectivity, otherwise ldap
        error instance.
    """
    if props is None:
        props = LDAPProps(server=server, port=port)
    try:
        c = LDAPConnector(props=props)
        lc = LDAPCommunicator(c)
        lc.bind()
        lc.unbind()
        return 'success'
    except ldap.LDAPError as error:
        return error


def md5digest(key):
    """Abbrev to create a md5 hex digest.

    :param key: Key to create a md5 hex digest for.
    :return digest: hex digest.
    """
    try:
        m = hashlib.md5()
    except ValueError:
        m = hashlib.md5(usedforsecurity=False)
    m.update(ensure_bytes(key))
    return m.hexdigest()


def cache_key(parts):
    def dec(p):
        if isinstance(p, bytes):
            p = p.decode('utf-8', 'replace')
        elif isinstance(p, (list, tuple)):
            p = u'-'.join([dec(_) for _ in p])
        elif not isinstance(p, six.text_type):
            p = six.text_type(p)
        return p
    return u'-'.join([dec(p) for p in parts])


def ensure_text(value):
    if value and not isinstance(value, six.text_type):
        value = value.decode('utf-8')
    return value


def ensure_bytes(value):
    if value and isinstance(value, six.text_type):
        value = value.encode('utf-8')
    return value


def ensure_bytes_py2(value):
    if six.PY2 and value and isinstance(value, six.text_type):  # pragma: no cover
        value = value.encode('utf-8')
    return value


class LDAPConnector(object):
    """Object is responsible for the LDAP connection.

    This Object knows about the LDAP Server to connect to, the authentication
    information and the protocol to use.

    TODO: tests for TLS/SSL Support - it should be functional.
    (see also properties.py)
    """

    def __init__(self, props=None):
        """Initialize LDAP connector.

        :param props: ``LDAPServerProperties`` instance.
        """
        self.protocol = ldap.VERSION3
        self._uri = props.uri
        self._bindDN = props.user
        self._bindPW = props.password
        self._cache = props.cache
        self._cachetimeout = props.timeout
        self._start_tls = props.start_tls
        self._ignore_cert = props.ignore_cert
        self._tls_cacert_file = props.tls_cacertfile
        self._retry_max = props.retry_max
        self._retry_delay = props.retry_delay

    def bind(self):
        """Bind to Server and return the Connection Object.
        """
        if self._ignore_cert:  # pragma: no cover
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        elif self._tls_cacert_file:  # pragma: no cover
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self._tls_cacert_file)
        self._con = ldap.ldapobject.ReconnectLDAPObject(
            self._uri,
            bytes_mode=False,
            bytes_strictness='silent',
            retry_max=self._retry_max,
            retry_delay=self._retry_delay
        )
        # Turning referrals off since they cause problems with MS Active
        # Directory More info: https://www.python-ldap.org/faq.html#usage
        self._con.set_option(ldap.OPT_REFERRALS, 0)
        self._con.protocol_version = self.protocol
        if self._start_tls:  # pragma: no cover
            # ignore in tests for now. nevertheless provide a test environment
            # for TLS and SSL later
            self._con.start_tls_s()
        self._con.simple_bind_s(self._bindDN, self._bindPW)
        return self._con

    def unbind(self):
        """Unbind from Server.
        """
        self._con.unbind_s()
        self._con = None


class LDAPCommunicator(object):
    """Class LDAPCommunicator is responsible for the communication with the
    LDAP Server.

    It provides methods to search, add, modify and delete entries in the
    directory.
    """

    def __init__(self, connector):
        """Initialize LDAP communicator.

        :param connector: ``LDAPConnector`` instance.
        """
        self.baseDN = ''
        self._connector = connector
        self._con = None
        self._cache = None
        if connector._cache:
            cachefactory = queryUtility(ICacheProviderFactory)
            if cachefactory is None:
                cachefactory = nullcacheProviderFactory
            cacheprovider = cachefactory()
            self._cache = ICacheManager(cacheprovider)
            self._cache.setTimeout(connector._cachetimeout)
            if not INullCacheProvider.providedBy(self._cache):
                logger.debug(
                    u"LDAP Caching activated for instance '{0:s}'. "
                    u"Use '{1:s}' as cache provider".format(
                        repr(self._cache),
                        repr(cacheprovider)
                    )
                )
            else:  # pragma: no cover
                logger.debug(
                    u"LDAP Caching activated for instance '{0:s}'.".format(
                        repr(self._cache),
                    )
                )

    def bind(self):
        """Bind to LDAP Server.
        """
        self._con = self._connector.bind()

    def unbind(self):
        """Unbind from LDAP Server.
        """
        self._connector.unbind()
        self._con = None

    def search(self, queryFilter, scope, baseDN=None,
               force_reload=False, attrlist=None, attrsonly=0,
               page_size=None, cookie=None):
        """Search the directory.

        :param queryFilter: LDAP query filter
        :param scope: LDAP search scope
        :param baseDN: Search base. Defaults to ``self.baseDN``
        :param force_reload: Force reload of result if cache enabled.
        :param attrlist: LDAP attrlist to query.
        :param attrsonly: Flag whether to return only attribute names, without
            corresponding values.
        :param page_size: Number of items per page, when doing pagination.
        :param cookie: Cookie string returned by previous search with
            pagination.
        """
        if baseDN is None:
            baseDN = self.baseDN
            if not baseDN:
                raise ValueError(u"baseDN unset.")
        if page_size:
            if cookie is None:
                cookie = ''
            pagedresults = ldap.controls.libldap.SimplePagedResultsControl(
                criticality=True, size=page_size, cookie=cookie)
            serverctrls = [pagedresults]
        else:
            if cookie:
                raise ValueError('cookie passed without page_size')
            serverctrls = []

        def _search(baseDN, scope, queryFilter,
                    attrlist, attrsonly, serverctrls):
            # we have to do async search to also retrieve server controls
            # in case we do pagination of results
            if type(attrlist) in (list, tuple):
                attrlist = [str(_) for _ in attrlist]
            try:
                msgid = self._con.search_ext(
                    baseDN,
                    scope,
                    queryFilter,
                    attrlist,
                    attrsonly,
                    serverctrls=serverctrls
                )
            except ldap.LDAPError as e:
                logger.warn(str(e))
                return []
            rtype, results, rmsgid, rctrls = self._con.result3(msgid)
            ctype = ldap.controls.libldap.SimplePagedResultsControl.controlType
            pctrls = [c for c in rctrls if c.controlType == ctype]
            if pctrls:
                return results, pctrls[0].cookie
            else:
                return results
        args = [baseDN, scope, queryFilter, attrlist, attrsonly, serverctrls]
        if self._cache:
            key_items = [
                self._connector._bindDN,
                baseDN,
                sorted(attrlist or []),
                attrsonly,
                queryFilter,
                scope,
                page_size,
                cookie
            ]
            return self._cache.getData(
                _search,
                md5digest(cache_key(key_items)),
                force_reload,
                args
            )
        return _search(*args)

    def add(self, dn, data):
        """Insert an entry into directory.

        :param dn: Adding DN
        :param data: Dict containing key/value pairs of entry attributes
        """
        attributes = [(k, v) for k, v in data.items()]
        self._con.add_s(dn, attributes)

    def modify(self, dn, modlist):
        """Modify an existing entry in the directory.

        Takes the DN of the entry and the modlist, which is a list of tuples
        containing modifation descriptions. The first element gives the type
        of the modification (MOD_REPLACE, MOD_DELETE, or MOD_ADD), the second
        gives the name of the field to modify, and the third gives the new
        value for the field (for MOD_ADD and MOD_REPLACE).
        """
        self._con.modify_s(dn, modlist)

    def delete(self, deleteDN):
        """Delete an entry from the directory.

        Take the DN to delete from the directory as argument.
        """
        self._con.delete_s(deleteDN)

    def passwd(self, userdn, oldpw, newpw):
        self._con.passwd_s(userdn, oldpw, newpw)


def main():
    """Use this module from command line for testing the connectivity to the
    LDAP Server.

    Expects server and port as arguments.
    """
    import sys
    if len(sys.argv) < 3:
        res = 'usage: python base.py [server] [port]'
    else:
        server, port = sys.argv[1:]
        res = testLDAPConnectivity(server, int(port))
    print(res)
    return res


if __name__ == "__main__":  # pragma: no cover
    main()
