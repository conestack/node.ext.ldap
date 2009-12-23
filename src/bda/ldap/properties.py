# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

class LDAPServerProperties(object):
    """Wrapper Class for LDAP Server connection properties.
    """
    
    def __init__(self,
                 server='localhost',
                 port=389,
                 user='',
                 password='',
                 cache=True,
                 timeout=43200):
        """Take the connection properties as arguments.
        
        @param server: servername, defaults to 'localhost'
        @param port: server port, defaults to 389
        @param user: username to bind, defaults to ''
        @param password: password to bind, defaults to ''
        @param cache: Bool wether to enable caching or not, defaults to True
        @param timeout: Cache timeout in seconds. only takes affect if cache
                        is enabled.
        """
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.cache = cache
        self.timeout = timeout

LDAPProps = LDAPServerProperties