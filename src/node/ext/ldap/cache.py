# -*- coding: utf-8 -*-
from zope.interface import implements
from zope.component import provideUtility
from bda.cache import (
    Memcached,
    NullCache,
)
from node.ext.ldap.interfaces import ICacheProviderFactory


def nullcacheProviderFactory():
    """Default cache provider factory.
    
    Does not cache anything.
    """
    return NullCache()


class MemcachedProviderFactory(object):
    """Memcached cache provider factory.
    """
    
    implements(ICacheProviderFactory)
    
    def __init__(self, servers=['127.0.0.1:11211']):
        self.servers = servers
    
    def __call__(self):
        return Memcached(self.servers)