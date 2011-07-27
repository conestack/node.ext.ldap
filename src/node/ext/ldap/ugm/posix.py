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


def uidNumber(node, id):
    num = 0
    for char in id:
        num += ord(char)
    return str(num)


gidNumber = uidNumber


def homeDirectory(node, id):
    return '/home/%s' % id


POSIX_DEFAULT_SHELL = '/bin/false'
def loginShell(node, id):
    return POSIX_DEFAULT_SHELL


def memberUid(node, id):
    # XXX: not tested right now. this changes as soon as the groups __setitem__
    #      plumbing hook is gone
    return ['nobody']                                       #pragma NO COVERAGE