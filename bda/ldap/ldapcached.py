# -*- coding: utf-8 -*-
#
# Copyright 2006-2008, BlueDynamics Alliance, Austria
# www.bluedynamics.com
#
# GNU General Public Licence Version 2 or later - see LICENCE.GPL

__docformat__ = 'plaintext'
__author__ = """Robert Niederreiter <rnix@squarewave.at>
                Johannes Raggam <johannes@bluedynamics.com>"""

from ldap.ldapobject import SimpleLDAPObject
import logging
from time import time
from plone.memoize import ram

logger = logging.getLogger('bda.ldap')

try:
    """Try to use memcached as caching storage
    """
    import memcache
    from plone.memoize.interfaces import ICacheChooser
    MEMCACHE_AVAILABLE = True
except ImportError:
    """Use default caching storage
    """
    logger.info('ldap-cache using default cache storage')
    MEMCACHE_AVAILABLE = False

if MEMCACHE_AVAILABLE:
    from zope.interface import directlyProvides
    from zope.component import provideUtility
    import zope.thread
    import os
    
    thread_local = zope.thread.local()
    def choose_cache(fun_name):
        global servers
        client=getattr(thread_local, "client", None)
        if client is None:
            servers=os.environ.get("MEMCACHE_SERVER",
                                    "127.0.0.1:11211").split(",")
            client=thread_local.client=memcache.Client(servers, debug=0)
        return ram.MemcacheAdapter(client)
    directlyProvides(choose_cache, ICacheChooser)
    provideUtility(choose_cache)
    ram.choose_cache = choose_cache
    logger.info('ldap-cache using memcached')
    


CACHE_TIMEOUT_SECONDS = 30*60

orig_search_ext = SimpleLDAPObject.search_ext
    
def _search_cachekey(method, self, *args, **kwargs):
    timeout = time() // CACHE_TIMEOUT_SECONDS
    iam = self.whoami_s() # also use bind creditentials for key
    key = [timeout] + [iam] + [arg for arg in args] + \
              [kwarg for kwarg in kwargs.items()]
    #print str(key)
    return str(key)

@ram.cache(_search_cachekey)
def search_ext(self, base, scope, filterstr='(objectClass=*)',
               attrlist=None, attrsonly=0, serverctrls=None, clientctrls=None,
               timeout=-1, sizelimit=0):
    ret = orig_search_ext(self, base, scope, filterstr, attrlist, attrsonly,
                          serverctrls, clientctrls, timeout, sizelimit)
    return ret

@ram.cache(_search_cachekey)
def search_ext_s(self, base, scope, filterstr='(objectClass=*)', attrlist=None,
                 attrsonly=0, serverctrls=None, clientctrls=None, timeout=-1,
                 sizelimit=0):
    msgid = orig_search_ext(self, base, scope, filterstr, attrlist, attrsonly,
                            serverctrls, clientctrls, timeout, sizelimit)
    return self.result(msgid, all=1, timeout=timeout)[1]

logger.info('REBINDING python-ldap search_ext for caching')

SimpleLDAPObject.search_ext = search_ext
SimpleLDAPObject.search_ext_s = search_ext_s
