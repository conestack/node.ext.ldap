# -*- coding: utf-8 -*-
"""
posixAccount
------------

- cn (must)
- uid (must)
- uidNumber (must)
- gidNumber (must)
- homeDirectory (must)
- userPassword ----> no default callback available
- loginShell
- gecos -----------> no default callback available
- description -----> no default callback available


posixGroup
----------

- cn (must)
- gidNumber(must)
- userPassword ----> no default callback available
- memberUid
- description -----> no default callback available
"""


def cn(node, uid):
    return uid.split('=')[1]


def uid(node, uid):
    return uid.split('=')[1]


UID_NUMBER = ''


def uidNumber(node, uid):
    """Default function gets called twice, second time without node.

    Bug. fix me.

    XXX: gets called by samba defaults
    """
    from node.ext.ldap.ugm import posix
    if not node:
        return posix.UID_NUMBER
    existing = node.search(criteria={'uidNumber': '*'}, attrlist=['uidNumber'])
    uidNumbers = [int(item[1]['uidNumber'][0]) for item in existing]
    uidNumbers.sort()
    if not len(uidNumbers):
        return '100'
    posix.UID_NUMBER = str(uidNumbers[-1] + 1)
    return posix.UID_NUMBER


GID_NUMBER = ''


def gidNumber(node, uid):
    """Default function gets called twice, second time without node.

    Bug. fix me.

    XXX: gets called by samba defaults
    """
    from node.ext.ldap.ugm import posix
    if not node:
        return posix.GID_NUMBER
    existing = node.search(criteria={'gidNumber': '*'}, attrlist=['gidNumber'])
    gidNumbers = [int(item[1]['gidNumber'][0]) for item in existing]
    gidNumbers.sort()
    if not gidNumbers:
        return '100'
    posix.GID_NUMBER = str(gidNumbers[-1] + 1)
    return posix.GID_NUMBER


def homeDirectory(node, uid):
    return '/home/%s' % uid.split('=')[1]


POSIX_DEFAULT_SHELL = '/bin/false'


def loginShell(node, uid):
    return POSIX_DEFAULT_SHELL


def memberUid(node, uid):
    # XXX: not tested right now. this changes as soon as the groups __setitem__
    #      plumbing hook is gone
    return ['nobody']                                       #pragma NO COVERAGE
