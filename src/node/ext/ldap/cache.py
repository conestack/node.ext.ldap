from zope.interface import implements
from zope.interface import implementer
from bda.cache import Memcached
from bda.cache import NullCache
from node.ext.ldap.interfaces import ICacheProviderFactory


@implementer(ICacheProviderFactory)
def nullcacheProviderFactory():
    """Default cache provider factory implementation for node.ext.ldap.
    
    Does not cache anything.
    """
    return NullCache()    


class MemcachedProviderFactory(object):
    """Memcached cache provider factory implementation for node.ext.ldap.
    
    Uses memcached, by default at localhost port 11211.
    """
    
    implements(ICacheProviderFactory)
    
    def __init__(self, servers=['127.0.0.1:11211']):
        self.servers = servers
    
    def __call__(self):
        return Memcached(self.servers)
