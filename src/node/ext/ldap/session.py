# -*- coding: utf-8 -*-
from node.ext.ldap import BASE
from node.ext.ldap import LDAPCommunicator
from node.ext.ldap import LDAPConnector
from node.ext.ldap import testLDAPConnectivity
import ldap


class LDAPSession(object):
    """LDAP Session binds always.

    all strings must be utf8 encoded!
    """

    def __init__(self, props):
        self._props = props
        connector = LDAPConnector(props=props)
        self._communicator = LDAPCommunicator(connector)

    def checkServerProperties(self):
        """Test if connection can be established.
        """
        res = testLDAPConnectivity(props=self._props)
        if res == 'success':
            return (True, 'OK')
        else:
            return (False, res)

    @property
    def baseDN(self):
        baseDN = self._communicator.baseDN
        return baseDN

    @baseDN.setter
    def baseDN(self, baseDN):
        """baseDN must be utf8-encoded.
        """
        self._communicator.baseDN = baseDN

    def ensure_connection(self):
        """If LDAP directory is down, bind again and retry given function.

        XXX: * Improve retry logic
             * Extend LDAPSession object to handle Fallback server(s)
        """
        if self._communicator._con is None:
            self._communicator.bind()

    def search(self, queryFilter='(objectClass=*)', scope=BASE, baseDN=None,
               force_reload=False, attrlist=None, attrsonly=0,
               page_size=None, cookie=None):
        if not queryFilter:
            # It makes no sense to really pass these to LDAP, therefore, we
            # interpret them as "don't filter" which in LDAP terms is
            # '(objectClass=*)'
            queryFilter = '(objectClass=*)'
        self.ensure_connection()
        res = self._communicator.search(queryFilter, scope, baseDN,
                                        force_reload, attrlist, attrsonly,
                                        page_size, cookie)
        if page_size:
            res, cookie = res
        # ActiveDirectory returns entries with dn None, which can be ignored
        res = filter(lambda x: x[0] is not None, res)
        if page_size:
            return res, cookie
        return res

    def add(self, dn, data):
        self.ensure_connection()
        self._communicator.add(dn, data)

    def authenticate(self, dn, pw):
        """Verify credentials, but don't rebind the session to that user
        """
        # Let's bypass connector/communicator until they are sorted out
        if self._props.ignore_cert:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        con = ldap.initialize(self._props.uri)
        # Turning referrals off since they cause problems with MS Active
        # Directory More info: https://www.python-ldap.org/faq.html#usage
        con.set_option(ldap.OPT_REFERRALS, 0)
        try:
            con.simple_bind_s(dn, pw)
        except (ldap.INVALID_CREDENTIALS, ldap.UNWILLING_TO_PERFORM):
            # The UNWILLING_TO_PERFORM event might be thrown, if you query a
            # local user named ``admin``, but the LDAP server is configured to
            # deny such queries. Instead of raising an exception, just ignore
            # this.
            return False
        else:
            return True

    def modify(self, dn, data, replace=False):
        """Modify an existing entry in the directory.

        :param dn: Modification DN
        :param data: Either list of 3 tuples (look at
            ``node.ext.ldap.base.LDAPCommunicator.modify`` for details), or a
            dictionary representing the entry or parts of the entry.
            XXX: dicts not yet
        :param replace: If set to True, replace entry at DN entirely with data.
        """
        self.ensure_connection()
        result = self._communicator.modify(dn, data)
        return result

    def delete(self, dn):
        self._communicator.delete(dn)

    def passwd(self, userdn, oldpw, newpw):
        self.ensure_connection()
        result = self._communicator.passwd(userdn, oldpw, newpw)
        return result

    def unbind(self):
        self._communicator.unbind()
