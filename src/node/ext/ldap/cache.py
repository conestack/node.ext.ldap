# -*- coding: utf-8 -*-
from bda.cache import Memcached
from bda.cache import NullCache
from node.ext.ldap.interfaces import ICacheProviderFactory
from zope.interface import implementer


def nullcacheProviderFactory():
    """Default cache provider factory.

    Does not cache anything.
    """
    return NullCache()


@implementer(ICacheProviderFactory)
class MemcachedProviderFactory(object):
    """Memcached cache provider factory.
    """

    def __init__(self, servers=['127.0.0.1:11211']):
        self.servers = servers

    def __call__(self):
        return Memcached(self.servers)
