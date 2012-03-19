# -*- coding: utf-8 -*-
import ldap
from node.utils import encode, decode
from node.ext.ldap import (
    BASE,
    LDAPConnector,
    LDAPCommunicator,
)
from node.ext.ldap.base import (
    testLDAPConnectivity,
    escape,
)


class LDAPSession(object):

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

    def _get_baseDN(self):
        baseDN = self._communicator.baseDN
        baseDN = decode(baseDN)
        return baseDN

    def _set_baseDN(self, baseDN):
        if isinstance(baseDN, str):
            # make sure its utf8
            baseDN = decode(baseDN)
        baseDN = encode(baseDN)
        self._communicator.baseDN = baseDN

    baseDN = property(_get_baseDN, _set_baseDN)

    def search(self, queryFilter='(objectClass=*)', scope=BASE, baseDN=None,
               force_reload=False, attrlist=None, attrsonly=0):

        #if self._props.escape_queries and baseDN is not None:
        #    baseDN = escape(baseDN)

        if queryFilter in ('', u'', None):
            # It makes no sense to really pass these to LDAP, therefore, we
            # interpret them as "don't filter" which in LDAP terms is
            # '(objectClass=*)'
            queryFilter = '(objectClass=*)'

        func = self._communicator.search
        res = self._perform(func, queryFilter, scope, baseDN,
                            force_reload, attrlist, attrsonly)

        # ActiveDirectory returns entries with dn None, which can be ignored
        res = filter(lambda x: x[0] is not None, res)
        return res

    def add(self, dn, data):
        func = self._communicator.add
        return self._perform(func, dn, data)

    def authenticate(self, dn, pw):
        """Verify credentials, but don't rebind the session to that user
        """
        # Let's bypass connector/communicator until they are sorted out
        con = ldap.initialize(self._props.uri)
        try:
            con.simple_bind_s(dn, pw)
        except ldap.INVALID_CREDENTIALS:
            return False
        else:
            return True

    def modify(self, dn, data, replace=False):
        """Modify an existing entry in the directory.

        dn
            Modification DN
        
        #data
        #    either list of 3 tuples (look at
        #    node.ext.ldap.base.LDAPCommunicator.modify for details), or
        #    a dictionary representing the entry or parts of the entry.
        #    XXX: dicts not yet
        
        replace
            if set to True, replace entry at DN entirely with data.
        """
        func = self._communicator.modify
        return self._perform(func, dn, data)

    def delete(self, dn):
        func = self._communicator.delete
        return self._perform(func, dn)

    def passwd(self, userdn, oldpw, newpw):
        func = self._communicator.passwd
        self._perform(func, userdn, oldpw, newpw)

    def unbind(self):
        self._communicator.unbind()

    def _perform(self, function, *args, **kwargs):
        """Try to perform the given function with the given argument.

        If LDAP directory is down, bind again and retry given function.

        XXX: * Improve retry logic in LDAPSession
             * Extend LDAPSession object to handle Fallback server(s)
        """

        # XXX BUG:
        # It is complete wrong to encode/ decode in here every string
        # LDAP handles binary data too and so fetching or setting binary
        # data fails. We need to refactor this part.

        args = encode(args)
        kwargs = encode(kwargs)
        if self._communicator._con is None:
            self._communicator.bind()
        return decode(function(*args, **kwargs))
