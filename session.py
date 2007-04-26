# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2007 by:
#     Blue Dynamics Alliance
#         * Klein & Partner KEG, Austria
#         * Squarewave Computing Robert Niederreiter, Austria
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

"""Module bda.ldap.session
"""

__version__ = '1.0'
__docformat__ = 'plaintext'
__author__ = """Robert Niederreiter <rnix@squarewave.at>,
                Georg Bernhard <g.bernhard@akbild.ac.at>"""

import ldap
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
        return self_perform(func, dn, data)
    
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
    