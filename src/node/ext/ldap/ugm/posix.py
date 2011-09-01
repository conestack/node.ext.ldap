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


def cn(node, id):
    return id


def uid(node, id):
    return id


UID_NUMBER = ''
def uidNumber(node, id):
    """Default function gets called twice, second time without node.
    
    Bug. fix me.
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


def gidNumber(node, id):
    if not node:
        return '' # XXX why?
    existing = node.search(criteria={'gidNumber': '*'}, attrlist=['gidNumber'])
    gidNumbers = [int(item[1]['gidNumber'][0]) for item in existing]
    gidNumbers.sort()
    if not gidNumbers:
        return '100'
    return str(gidNumbers[-1] + 1)


def homeDirectory(node, id):
    return '/home/%s' % id


POSIX_DEFAULT_SHELL = '/bin/false'
def loginShell(node, id):
    return POSIX_DEFAULT_SHELL


def memberUid(node, id):
    # XXX: not tested right now. this changes as soon as the groups __setitem__
    #      plumbing hook is gone
    return ['nobody']                                       #pragma NO COVERAGE