#
# Copyright 2008, Blue Dynamics Alliance, Austria - http://bluedynamics.com
#
# GNU General Public Licence Version 2 or later

"""Module bda.ldap.properties

This module provides a Class for wrapping LDAP directory Server connection
properties.
"""

__docformat__ = 'plaintext'
__author__ = """Robert Niederreiter <rnix@squarewave.at>"""

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
