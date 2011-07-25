###############################################################################
# shadow account related
#
# - userPassword -----> no default callback available
# - description ------> no default callback available
# - shadowFlag
# - shadowMin
# - shadowMax
# - shadowWarning
# - shadowInactive
# - shadowLastChange
# - shadowExpire

def shadowFlag(node, id):
    return '0'

def shadowMin(node, id): 
    """Min number of days between password changes.
    """
    return '0'

def shadowMax(node, id): 
    """max number of days password is valid.
    """
    return '99999'

def shadowWarning(node, id): 
    """Numer of days before password expiry to warn user.
    """
    return '0'

def shadowInactive(node, id): 
    """Numer of days to allow account to be inactive.
    """
    return '99999'

def shadowLastChange(node, id): 
    """Last change of shadow info, int value.
    """
    return '12011'

def shadowExpire(node, id): 
    """Absolute date to expire account counted in days since 1.1.1970
    """
    return '99999'