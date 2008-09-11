# -*- coding: utf-8 -*-
#
# Copyright 2006-2008, BlueDynamics Alliance, Austria
# www.bluedynamics.com
#
# GNU General Public Licence Version 2 or later - see LICENCE.GPL

__docformat__ = 'plaintext'
__author__ = """Robert Niederreiter <rnix@squarewave.at>
                Hannes Raggam <johannes@bluedynamics.com>"""

import ldap

xldap = ldap
orginsearch = ldap.search

def search(*args, **kwargs):
    key = ''.join(str(arg) for arg in args)
    key = '%s%s' % (key, ''.join('%s%s', str(key), str(value) \
                                     in kwargs.items()))
    cached = _getCached(key)
    if cached:
        return cached
    res = orginsearch(*args, **kwargs)
    _cache(key, res)
    return res

def _getCached(key):
    return None

def _cache(key, value):
    return

xldap.search = search