# -*- coding: utf-8 -*-
try:
    import ldap
except ImportError:                                         #pragma NO COVERAGE
    e =  u"node.ext.ldap requires a working "               #pragma NO COVERAGE
    e += u"python-ldap installation."                       #pragma NO COVERAGE
    raise ImportError, e                                    #pragma NO COVERAGE
import logging
from zope.component import queryUtility
from bda.cache import ICacheManager
from node.ext.ldap.interfaces import ICacheProviderFactory
from node.ext.ldap.properties import LDAPProps
from node.ext.ldap.cache import nullcacheProviderFactory
from node.ext.ldap.scope import BASE, ONELEVEL, SUBTREE, SCOPES


logger = logging.getLogger('node.ext.ldap')


def testLDAPConnectivity(server=None, port=None, props=None):
    """Function to test the availability of the LDAP Server.
    
    server
        Server IP or name
    
    port
        LDAP port
    
    props
        LDAPProps object. If given, server and port are ignored.
    """
    if props is None:
        props = LDAPProps(server=server, port=port)
    try:
        c = LDAPConnector(props=props)
        lc = LDAPCommunicator(c)
        lc.bind()
        lc.unbind()
        return 'success'
    except ldap.LDAPError, error:
        return error


def md5digest(key):
    """Needed to support both, python 2.4 and python >=2.5

    Will be remove when python 2.4 support is dropped.
    """
    try:
        # in python >=2.5
        import hashlib
    except ImportError:                                     #pragma NO COVERAGE
        # fallback if python 2.4
        import md5                                          #pragma NO COVERAGE
        return md5.new(key).hexdigest()                     #pragma NO COVERAGE
    m = hashlib.md5()
    m.update(key)
    return m.hexdigest()


def decode_utf8(value):
    if value and not isinstance(value, unicode):
        value = value.decode('utf-8')
    return value


def encode_utf8(value):
    if value and isinstance(value, unicode):
        value = value.encode('utf-8')
    return value


def escape(value):
    """Escapes a value, note that this is documented for AD queries, but 
    not for OpenLDAP etc, but hopefully they work in the same manner.
    """
    # don't know how to 'find' NUL = \\0
    #'*' :'\\2a',
    replacements = {
        '(' :'\\28',
        ')' :'\\29',
        '\\':'\\5c',
        '/' :'\\2f',
    }
    for key, val in replacements.items():
        value = value.replace(key, val)
    return value


class LDAPConnector(object):
    """Object is responsible for the LDAP connection.

    This Object knows about the LDAP Server to connect to, the authentication
    information and the protocol to use.

    TODO: tests for TLS/SSL Support - it should be functional. 
    (see also properties.py)
    """

    def __init__(self,
                 server=None,
                 port=None,
                 bindDN=None,
                 bindPW=None,
                 cache=True,
                 cachetimeout=43200,
                 props=None):
        """Initialize LDAPConnector.

        Signature Deprecated: Signature will take ``LDAPProps``
                              object only instead of current kwargs in future.
                              This will be changed in Version 1.0.
        """
        self.protocol = ldap.VERSION3
        if props is None:
            # old
            logging.warn(u"Deprecated usage of ``LDAPConnector.__init__``. "
                         u"please pass ``LDAPProps`` object instead of "
                         u"separate settings.")
            self._uri = "ldap://%s:%d/" % (server, port)
            self._bindDN = bindDN
            self._bindPW = bindPW
            self._cache = cache
            self._cachetimeout = cachetimeout
            self._start_tls = 0
        else:
            # new
            self._uri = props.uri
            self._bindDN = props.user
            self._bindPW = props.password
            self._cache = props.cache
            self._cachetimeout = props.timeout
            self._start_tls = props.start_tls
            #self._escape_queries = props.escape_queries

    def bind(self):
        """Bind to Server and return the Connection Object.
        """
        self._con = ldap.initialize(self._uri)
        self._con.protocol_version = self.protocol
        if self._start_tls:
            # ignore in tests for now. nevertheless provide a test environment
            # for TLS and SSL later
            self._con.start_tls_s()                         #pragma NO COVERAGE
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
        """
        connector
            LDAPConnector instance.
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
            logger.debug(u"LDAP Caching activated for instance '%s'. Use '%s' "
                          "as cache provider" % (repr(self._cache),
                                                 repr(cacheprovider)))

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
               force_reload=False, attrlist=None, attrsonly=0):
        """Search the directory.

        queryFilter
            LDAP query filter
        
        scope
            LDAP search scope
        
        baseDN
            Search base. Defaults to ``self.baseDN``
        
        force_reload
            Force reload of result if cache enabled.
        
        attrlist
            LDAP attrlist to query.
        
        attrsonly
            Flag whether to return only attribute names, without corresponding
            values.
        """
        if baseDN is None:
            baseDN = self.baseDN
            if not baseDN:
                raise ValueError(u"baseDN unset.")
        
        #if self._connector._escape_queries:
        #    queryFilter = self._escape_query(queryFilter)
        
        if self._cache:
            # XXX: Consider attrlist and attrsonly in cachekey.
            key = '%s-%s-%s-%i' % (self._connector._bindDN,
                                   baseDN,
                                   queryFilter,
                                   scope)
            key = md5digest(key)
            args = [baseDN, scope, queryFilter, attrlist, attrsonly]
            return self._cache.getData(self._con.search_s, key,
                                       force_reload, args)
        return self._con.search_s(baseDN, scope, queryFilter,
                                  attrlist, attrsonly)

    def add(self, dn, data):
        """Insert an entry into directory.
        
        dn
            adding DN
        
        data
            dict containing key/value pairs of entry attributes
        """
        attributes = [ (k,v) for k,v in data.items() ]
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
        print 'usage: python base.py [server] [port]'
    else:
        server, port = sys.argv[1:]
        print testLDAPConnectivity(server, int(port))


if __name__ == "__main__":
    main()                                                  #pragma NO COVERAGE
