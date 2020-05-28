from bda.cache.memcached import Memcached
from bda.cache.nullcache import NullCache
from node.ext.ldap import testing
from node.ext.ldap.cache import MemcachedProviderFactory
from node.ext.ldap.cache import nullcacheProviderFactory
from node.ext.ldap.interfaces import ICacheProviderFactory
from node.tests import NodeTestCase
from zope.interface import registry


class TestCache(NodeTestCase):
    layer = testing.LDIF_data

    def test_cache(self):
        # Default cache provider factory, userd if caching is enabled and no
        # ``ICacheProviderFactory`` utility is registered.::
        cache = nullcacheProviderFactory()
        self.assertTrue(isinstance(cache, NullCache))

        # Cache provider factory for Memcached backend. Instanciate class
        # and register as ``ICacheProviderFactory`` utility if Memcached is the
        # desired caching backend. For providing other backends, read
        # documentation of ``bda.cache``
        cache_factory = MemcachedProviderFactory()

        components = registry.Components('comps')
        components.registerUtility(cache_factory)

        factory = components.queryUtility(ICacheProviderFactory)
        self.assertTrue(isinstance(factory, MemcachedProviderFactory))

        cache = factory()
        self.assertTrue(isinstance(cache, Memcached))

        components.unregisterUtility(cache_factory)
