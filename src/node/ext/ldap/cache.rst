node.ext.ldap.cache
===================

Default cache provider factory, userd if caching is enabled and no
``ICacheProviderFactory`` utility is registered.::

    >>> from node.ext.ldap.cache import nullcacheProviderFactory
    >>> nullcacheProviderFactory()
    <bda.cache.nullcache.NullCache object at ...>

Cache provider factory for Memcached backend. Instanciate class
and register as ``ICacheProviderFactory`` utility if Memcached is the desired
caching backend. For providing other backends, read documentation of
``bda.cache``::

    >>> from node.ext.ldap.cache import MemcachedProviderFactory
    >>> cache_factory = MemcachedProviderFactory()
    
    >>> from zope.component import registry
    >>> components = registry.Components('comps')
    >>> components.registerUtility(cache_factory)
    
    >>> from node.ext.ldap.interfaces import ICacheProviderFactory
    >>> factory = components.queryUtility(ICacheProviderFactory)
    >>> factory
    <node.ext.ldap.cache.MemcachedProviderFactory object at ...>
    
    >>> factory()
    <bda.cache.memcached.Memcached object at ...>

Cleanup.::

    >>> components.unregisterUtility(cache_factory)
    True
