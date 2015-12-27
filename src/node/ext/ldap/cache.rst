node.ext.ldap.cache
===================

Test related imports::

    >>> from node.ext.ldap.cache import MemcachedProviderFactory
    >>> from node.ext.ldap.cache import nullcacheProviderFactory
    >>> from node.ext.ldap.interfaces import ICacheProviderFactory
    >>> from zope.component import registry

Default cache provider factory, userd if caching is enabled and no
``ICacheProviderFactory`` utility is registered.::

    >>> nullcacheProviderFactory()
    <bda.cache.nullcache.NullCache object at ...>

Cache provider factory for Memcached backend. Instanciate class
and register as ``ICacheProviderFactory`` utility if Memcached is the desired
caching backend. For providing other backends, read documentation of
``bda.cache``::

    >>> cache_factory = MemcachedProviderFactory()

    >>> components = registry.Components('comps')
    >>> components.registerUtility(cache_factory)

    >>> factory = components.queryUtility(ICacheProviderFactory)
    >>> factory
    <node.ext.ldap.cache.MemcachedProviderFactory object at ...>

    >>> factory()
    <bda.cache.memcached.Memcached object at ...>

Cleanup.::

    >>> components.unregisterUtility(cache_factory)
    True
