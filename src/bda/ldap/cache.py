# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

from zope.interface import implements
from bda.cache import Memcached
from interfaces import ICacheProviderFactory

class MemcachedProviderFactory(object):
    """Default cache provider factory implementation for bda.ldap.
    """
    
    implements(ICacheProviderFactory)
    
    def __call__(self):
        return Memcached(['127.0.0.1:11211'])