# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

from zope.interface import implements
from zope.interface import implementer
from bda.cache import Memcached
from bda.cache import NullCache
from bda.ldap.interfaces import ICacheProviderFactory

@implementer(ICacheProviderFactory)
def nullcacheProviderFactory():
    """Default cache provider factory implementation for bda.ldap.
    
    Does not cache anything.
    """
    return NullCache()    

class MemcachedProviderFactory(object):
    """Memcached cache provider factory implementation for bda.ldap.
    
    Uses memcached, by default at localhost port 11211.
    """
    
    implements(ICacheProviderFactory)
    
    def __init__(self, servers=['127.0.0.1:11211']):
        self.servers = servers
    
    def __call__(self):
        return Memcached(self.servers)