import smbpasswd
import posix

###############################################################################
# samba utils

def sambaNTPassword(passwd):              
    return smbpasswd.nthash(passwd)

def sambaLMPassword(passwd):
    return smbpasswd.lmhash(passwd)


###############################################################################
# samba user related
#
# - sambaSID
# - sambaPrimaryGroupSID
# - sambaPwdMustChange ------> no default callback available
# - sambaPwdCanChange -------> no default callback available
# - sambaPwdLastSet ---------> no default callback available
# - sambaKickoffTime --------> no default callback available
# - sambaLogOnTime ----------> no default callback available
# - sambaLogoffTime ---------> no default callback available
# - sambaAcctFlags
# - sambaNTPassword
# - sambaLMPassword
# - sambaHomeDrive ----------> no default callback available
# - sambaHomePath -----------> no default callback available
# - sambaLogonScript---------> no default callback available
# - sambaProfilePath---------> no default callback available
# - sambaUserWorkstations----> no default callback available
# - sambaDomainName
# - sambaPasswordHistory ----> no default callback available
# - sambaMungedDial ---------> no default callback available
# - sambaBadPasswordCount ---> no default callback available
# - sambaBadPasswordTime ----> no default callback available
# - sambaLogonHours ---------> no default callback available
# - displayName -------------> no default callback available

# net getlocalsid | net getlocalsid [domain]
SAMBA_LOCAL_SID = 'S-1-5-21-1234567890-1234567890-1234567890'

def sambaUserSID(node, id):
    """uid * 2 + 1000 = rid for users
    """
    rid = int(posix.uidNumber(None, id)) * 2 + 1000
    return SAMBA_LOCAL_SID + '-' + str(rid)

SAMBA_DEFAULT_DOMAIN = 'CONE_UGM'
def sambaDomainName(node, id):
    return SAMBA_DEFAULT_DOMAIN

SAMBA_PRIMARY_GROUP_SID = 'S-1-5-21-1234567890-1234567890-1234567890-123'
def sambaPrimaryGroupSID(node, id):
    return SAMBA_PRIMARY_GROUP_SID

SAMBA_DEFAULT_ACCOUNT_FLAGS = '[U]'
def sambaAcctFlags(node, id):
    return SAMBA_DEFAULT_ACCOUNT_FLAGS


###############################################################################
# samba group related
#
# - gidNumber
# - sambaSID
# - sambaGroupType
# - displayName ------> no default callback available
# - description ------> no default callback available
# - sambaSIDList -----> no default callback available

def sambaGroupSID(node, id):
    """gid * 2 + 1001 = rid for groups
    """
    rid = int(posix.gidNumber(None, id)) * 2 + 1000
    return SAMBA_LOCAL_SID + '-' + str(rid)

def sambaGroupType(node, id):
    return '2'