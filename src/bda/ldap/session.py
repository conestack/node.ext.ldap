# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

import ldap
from bda.ldap import (
    LDAPConnector,
    LDAPCommunicator,
)
from bda.ldap.base import testLDAPConnectivity

class LDAPSession(object):
    
    def __init__(self, props):
        connector = LDAPConnector(props.server,
                                  props.port,
                                  props.user,
                                  props.password,
                                  props.cache,
                                  props.timeout)
        self._communicator = LDAPCommunicator(connector)
        self.ldap_encoding = props.encoding
    
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
        self._communicator.baseDN = baseDN
    
    def _get_baseDN(self):
        return self._communicator.baseDN
    
    def _set_baseDN(self, baseDN):
        self._communicator.baseDN = baseDN
    
    baseDN = property(_get_baseDN, _set_baseDN)
    
    def search(self, queryFilter, scope, baseDN=None,
               force_reload=False, attrlist=None, attrsonly=0):
        # default filter for python-ldap methods is '(objectClass=*)', should be
        # the same here - alternative: kw arg, problem: scope
        if queryFilter in ('', u'', None):
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
    
    def _encode(self, arg):
        """Return an encoded copy of the argument
        - strs are decoded and reencode to make sure they conform to the
          encoding
        - unicodes are encoded as str according to ldap_encoding
        - lists/tuples/dicts are recursively worked on
        - everything else is left untouched
        """
        if isinstance(arg, (list, tuple)):
            arg = arg.__class__(map(self._encode, arg))
        elif isinstance(arg, dict):
            arg = dict(
                [self._encode(t) for t in arg.iteritems()]
                )
        elif isinstance(arg, str):
            arg = self._encode(
                    self._decode(arg)
                    )
        elif isinstance(arg, unicode):
            arg = arg.encode(self.ldap_encoding)
        return arg

    def _decode(self, arg):
        if isinstance(arg, (list, tuple)):
            arg = arg.__class__(map(self._decode, arg))
        elif isinstance(arg, dict):
            arg = dict(
                [self._decode(t) for t in arg.iteritems()]
                )
        elif isinstance(arg, str):
            arg = arg.decode(self.ldap_encoding)
        return arg

    def _perform(self, function, *args, **kwargs):
        """Try to perform the given function with the given argument.
        
        If LDAP directory is down, bind again and retry given function.
        
        XXX: * Improve retry logic in LDAPSession 
             * Extend LDAPSession object to handle Fallback server(s)
        """
        args = self._encode(args)
        kwargs = self._encode(kwargs)

        if self._communicator._con is None:
            self._communicator.bind()
        try:
            return self._decode(function(*args, **kwargs))
        except ldap.SERVER_DOWN:
            self._communicator.bind()
            return self._decode(function(*args, **kwargs))
