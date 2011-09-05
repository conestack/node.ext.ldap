"""
shadowAccount
-------------

- uid (must)
- userPassword -----> no default callback available
- shadowLastChange 
- shadowMin
- shadowMax
- shadowWarning
- shadowInactive
- shadowExpire
- shadowFlag
- description ------> no default callback available
"""


SHADOW_DEFAULT_FLAG = '0'
def shadowFlag(node, uid):
    return SHADOW_DEFAULT_FLAG


SHADOW_DEFAULT_MIN = '0'
def shadowMin(node, uid): 
    """Min number of days between password changes.
    """
    return SHADOW_DEFAULT_MIN


SHADOW_DEFAULT_MAX = '99999'
def shadowMax(node, uid): 
    """max number of days password is valid.
    """
    return SHADOW_DEFAULT_MAX


SHADOW_DEFAULT_WARNING = '0'
def shadowWarning(node, uid): 
    """Numer of days before password expires to warn user.
    """
    return SHADOW_DEFAULT_WARNING


SHADOW_DEFAULT_INACTIVE = '99999'
def shadowInactive(node, uid): 
    """Numer of days to allow account to be inactive.
    """
    return SHADOW_DEFAULT_INACTIVE


def shadowLastChange(node, uid): 
    """Last change of shadow info, int value.
    
    XXX: compute.
    """
    return '12011'


SHADOW_DEFAULT_EXPIRE = '99999'
def shadowExpire(node, uid): 
    """Absolute date to expire account counted in days since 1.1.1970
    """
    return SHADOW_DEFAULT_EXPIRE