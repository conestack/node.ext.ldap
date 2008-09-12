# -*- coding: utf-8 -*-
#
# Copyright 2006-2008, BlueDynamics Alliance, Austria
# www.bluedynamics.com
#
# GNU General Public Licence Version 2 or later - see LICENCE.GPL

__docformat__ = 'plaintext'
__author__ = """Robert Niederreiter <rnix@squarewave.at>,
                Georg Bernhard <g.bernhard@akbild.ac.at>,
                Florian Friesdorf <flo@chaoflow.net>"""

from ldap import SERVER_DOWN

from base import LDAPConnector
from base import LDAPCommunicator
from base import testLDAPConnectivity

class LDAPSession(object):
    
    def __init__(self, serverProps):
        connector = LDAPConnector(serverProps.server,
                                  serverProps.port,
                                  serverProps.user,
                                  serverProps.password)
        self.communicator = LDAPCommunicator(connector)
    
    def checkServerProperties(self):
        """ Test if connection can be established.
        """
        res = testLDAPConnectivity(\
                self.communicator._connector.server,
                self.communicator._connector.port)
        if res == 'success':
            return (True, 'OK')
        else:
            return (False, res)
    
    def setBaseDN(self, baseDN):
        """Set the base DN you want to work on.
        """
        self.communicator.setBaseDN(baseDN)
    
    def search(self, queryFilter, scope, baseDN=None):
        """Search the directory.
        
        Look at bda.ldap.base.LDAPCommunicator.search() for details.
        """
        func = self.communicator.search
        return self._perform(func, queryFilter, scope, baseDN)
    
    def add(self, dn, data):
        """Insert an entry into directory.
        
        Look at bda.ldap.base.LDAPCommunicator.add() for details.
        """
        func = self.communicator.add
        return self._perform(func, dn, data)
    
    def modify(self, dn, data):
        """Modify an existing entry in the directory.
        
        Look at bda.ldap.base.LDAPCommunicator.modify() for details.
        """
        func = self.communicator.modify
        return self._perform(func, dn, data)
    
    def delete(self, dn):
        """Delete an entry from the directory.
        
        Take the DN to delete from the directory as argument.
        """
        func = self.communicator.delete
        return self._perform(func, dn)
    
    def _perform(self, function, *args, **kwargs):
        """Try to perform the given function with the given argument.
        
        If LDAP directory is down, bind again and retry given function.
        """
        if self.communicator._con is None:
            self.communicator.bind()
        try:
            return function(*args, **kwargs)
        except ldap.SERVER_DOWN:
            self.communicator.bind()
            return function(*args, **kwargs)
    