# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

import ldap
from bda.ldap import (
    BASE,
    LDAPConnector,
    LDAPCommunicator,
)
from bda.ldap.base import testLDAPConnectivity
from bda.ldap.strcodec import encode, decode

class LDAPSession(object):
    
    def __init__(self, props):
        connector = LDAPConnector(props.server,
                                  props.port,
                                  props.user,
                                  props.password,
                                  props.cache,
                                  props.timeout)
        self._communicator = LDAPCommunicator(connector)
    
    def checkServerProperties(self):
        """Test if connection can be established.
        """
        res = testLDAPConnectivity(
                  self._communicator._connector._server,
                  self._communicator._connector._port)
        if res == 'success':
            return (True, 'OK')
        else:
            return (False, res)
    
    def setBaseDN(self, baseDN):
        """Set the base DN you want to work on.
        
        Deprecated: This function will be removed in version 1.5. Use
                    ``baseDN`` property directly instead.
        """
        self.baseDN = baseDN
    
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
        # It makes no sense to really pass these to LDAP, therefore, we
        # interpret them as "don't filter" which in LDAP terms is
        # '(objectClass=*)'
        if queryFilter in ('', u'', None):
            queryFilter='(objectClass=*)'
        func = self._communicator.search
        res = self._perform(func, queryFilter, scope, baseDN,
                            force_reload, attrlist, attrsonly)
        # ActiveDirectory returns entries with dn None, which can be ignored
        res = filter(lambda x: x[0] is not None, res)
        return res
    
    def add(self, dn, data):
        func = self._communicator.add
        return self._perform(func, dn, data)
    
    def modify(self, dn, data, replace=False):
        """Modify an existing entry in the directory.
        
        @param dn: Modification DN
        @param data: either list of 3 tuples (look at
                     bda.ldap.base.LDAPCommunicator.modify for details), or
                     a dictionary representing the entry or parts of the entry.
        @param replace: if set to True, replace entry at DN entirely with data.
        
        XXX: implement described behaviour for data
        """
        func = self._communicator.modify
        return self._perform(func, dn, data)
    
    def delete(self, dn):
        func = self._communicator.delete
        return self._perform(func, dn)
    
    def unbind(self):
        self._communicator.unbind()
    
    def _perform(self, function, *args, **kwargs):
        """Try to perform the given function with the given argument.
        
        If LDAP directory is down, bind again and retry given function.
        
        XXX: * Improve retry logic in LDAPSession 
             * Extend LDAPSession object to handle Fallback server(s)
        """
        args = encode(args)
        kwargs = encode(kwargs)

        if self._communicator._con is None:
            self._communicator.bind()
        try:
            return decode(function(*args, **kwargs))
        except ldap.SERVER_DOWN:
            self._communicator.bind()
            return decode(function(*args, **kwargs))
