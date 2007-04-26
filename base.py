# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2007 by BlueDynamics Alliance, Austria
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

"""Module bda.ldap.base

This module provides Classes for communicating with an LDAP directory Server
and for managing the directory itself.

depends on python-ldap.
"""

__version__ = '1.0'
__docformat__ = 'plaintext'
__author__ = """Robert Niederreiter <rnix@squarewave.at>"""

import ldap

BASE = ldap.SCOPE_BASE
ONELEVEL = ldap.SCOPE_ONELEVEL
SUBTREE = ldap.SCOPE_SUBTREE
SCOPES = [BASE, ONELEVEL, SUBTREE]

def testLDAPConnectivity(server, port):
    """Function to test the availability of the LDAP Server.
    """
    try:
        c = LDAPConnector(server, port, '', '')
        lc = LDAPCommunicator(c)
        lc.bind()
        lc.unbind()
        return 'success'
    except ldap.LDAPError, error:
        return error


class LDAPConnector(object):
    """Object is responsible for the LDAP connection.
    
    This Object knows about the LDAP Server to connect to, the authentication
    information and the protocol to use.
    
    TODO: TLS/SSL Support.
    
    Direct Usage - no need for this in general:
        
    c = LDAPConnector('localhost', 389, 'cn=admin,dc=foo,dc=bar', 'secret')
    connection = c.bind()
    # do something with connection
    ...
    c.unbind() 
    """
    
    def __init__(self, server, port, bindDN, bindPW):
        """Define Server, Port, Bind DN and Bind PW to use.
        """
        self.protocol = ldap.VERSION3
        self.server = server
        self.port = port
        self.bindDN = bindDN
        self._bindPW = bindPW
    
    def setProtocol(self, protocol):
        """Set the LDAP Protocol Version to use.
        
        For example ldap.VERSION2.
        """
        self.protocol = protocol
    
    def bind(self):
        """Bind to Server and return the Connection Object.
        """
        protocol, bindDN, _bindPW = self.protocol, self.bindDN, self._bindPW
        self._con = ldap.open(self.server, self.port)
        self._con.protocol_version = protocol
        self._con.simple_bind(bindDN, _bindPW)
        return self._con
    
    def unbind(self):
        """Unbind from the LDAP Server.
        """
        self._con.unbind()
        self._con = None
        
    
class LDAPCommunicator(object):
    """Class LDAPCommunicator is responsible for the communication with the
    LDAP Server.
    
    It provides methods to search, add, modify and delete entries in the
    directory.
    
    Usage:

    c = LDAPConnector('localhost', 389, 'cn=admin,dc=foo,dc=bar', 'secret')
    lc = LDAPCommunicator(c)
    lc.setBaseDN('ou=customers,dc=foo,dc=bar')
    lc.bind()
    result = lc.search('uid=user@foo.bar', lc.SUBTREE)
    # do soething with result
    ...
    lc.unbind()
    """
    
    def __init__(self, connector):
        """Takes LDAPConnector object as argument.
        """
        self._connector = connector
        self._con = None
        self._baseDN = ''
        
    def bind(self):
        """Bind to LDAP Server.
        """
        self._con = self._connector.bind()
        
    def unbind(self):
        """Unbind from LDAP Server.
        """
        self._connector.unbind()
        self._con = None
        
    def setBaseDN(self, baseDN):
        """Set the base DN you want to work on.
        """
        self._baseDN = baseDN
        
    def getBaseDN(self):
        """Returns the current set base DN.
        """
        return self._baseDN
        
    def search(self, queryFilter, scope, baseDN=None):
        """Search the directory.
        
        Take the query filter, the search scope and optional the base DN if
        you want to use another base DN than set by setBaseDN() for this
        oparation.
        """
        if baseDN is None:
            baseDN = self._baseDN
        return self._con.search_s(baseDN, scope, queryFilter)
    
    def add(self, dn, data):
        """Insert an entry into directory.
        
        Takes the DN of the entry and the data this object contains. data is a
        dictionary and looks ike this:
        
        data = {
            'uid':'foo',
            'givenname':'foo',
            'cn':'foo 0815',
            'sn':'bar',
            'telephonenumber':'123-4567',
            'facsimiletelephonenumber':'987-6543',
            'objectclass':('Remote-Address','person', 'Top'),
            'physicaldeliveryofficename':'Development',
            'mail':'foo@bar.org',
            'title':'programmer',
        }
        """
        attributes = [ (k,v) for k,v in data.items() ]
        self._con.add_s(dn, attributes)    
        
    def modify(self, dn, data):
        """Modify an existing entry in the directory.
        
        The first argument is a string containing the dn of the object 
        to modify, and the second argument is a list of tuples containing 
        modifation descriptions. The first element gives the type of the 
        modification (MOD_REPLACE, MOD_DELETE, or MOD_ADD), the second gives 
        the name of the field to modify, and the third gives the new value 
        for the field (for MOD_ADD and MOD_REPLACE).
        """
        self._con.modify_s(dn, data)
        
    def delete(self, deleteDN):
        """Delete an entry from the directory.
        
        Take the DN to delete from the directory as argument.
        """
        self._con.delete_s(deleteDN)

if __name__ == "__main__":
    """Use this module from command line for testing the connectivity to the
    LDAP Server.
    
    Expects server and port as arguments."""
    
    import sys
    if len(sys.argv) < 3:
        print 'usage: python base.py [server] [port]'
    else:
        server, port = sys.argv[1:]
        print testLDAPConnectivity(server, int(port))
