#
# Copyright 2008, Blue Dynamics Alliance, Austria - http://bluedynamics.com
#
# GNU General Public Licence Version 2 or later

__docformat__ = 'plaintext'
__author__ = """Robert Niederreiter <rnix@squarewave.at>"""

from zope.interface import implements

from bda.cache import Memcached

from interfaces import ICacheProviderFactory

class MemcachedProviderFactory(object):
    """Default cache provider factory implementation for bda.ldap.
    """
    
    implements(ICacheProviderFactory)
    
    def __call__(self):
        return Memcached(['127.0.0.1:11211'])