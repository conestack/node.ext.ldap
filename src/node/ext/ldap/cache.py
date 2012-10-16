# -*- coding: utf-8 -*-
from zope.interface import implementer
from bda.cache import (
    Memcached,
    NullCache,
)
from .interfaces import ICacheProviderFactory


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
