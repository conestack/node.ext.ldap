# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

"""Module bda.ldap.properties

This module provides a Class for wrapping LDAP directory Server connection
properties.
"""

class LDAPServerProperties(object):
    """Wrapper Class for LDAP Server connection properties.
    """
    
    def __init__(self,
                 server='localhost',
                 port=389,
                 user='',
                 password='',
                 cache=True):
        """Take the connection properties as arguments.
        
        @param server: servername, defaults to 'localhost'
        @param port: server port, defaults to 389
        @param user: username to bind, defaults to ''
        @param password: password to bind, defaults to ''
        @param cache: Bool wether to enable caching or not, defaults to True
        """
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.cache = cache