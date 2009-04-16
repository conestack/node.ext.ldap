# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

"""Module bda.ldap.properties

This module provides a Class for wrapping LDAP directory Server connection
properties.
"""

class LDAPServerProperties(object):
    """Wrapper Class for LDAP Server connection properties.
    """
    
    def __init__(self, server='localhost', port=389, user='', password=''):
        """Take the connection properties as arguments.
        
        Defaults are:
            server: 'localhost'
            port: 389
            user: ''
            pass: ''
        """
        self.server = server
        self.port = port
        self.user = user
        self.password = password