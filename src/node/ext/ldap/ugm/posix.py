from bda.basen import base62


###############################################################################
# posix user related
#
# - uidNumber
# - gidNumber
# - uid -------------> no default callback available
# - cn --------------> no default callback available
# - userPassword ----> no default callback available
# - homeDirectory
# - loginShell
# - gecos -----------> no default callback available
# - description -----> no default callback available

def uidNumber(node, id):
    term = base62(id)
    return str(int(term))

def posixGidNumber(node, id):
    term = base62(id)
    return str(int(term))

DEFAULT_GID = '12345'
def gidNumber(node, id):
    return DEFAULT_GID

def homeDirectory(node, id):
    return '/home/%s' % id

DEFAULT_SHELL = '/bin/false'
def loginShell(node, id):
    return DEFAULT_SHELL


###############################################################################
# posix group related
#
# - memberUid

def memberUid(node, id):
    return ['nobody']