# -*- coding: utf-8 -*-
"""
sambaSamAccount
---------------

- sambaSID (must)
- cn
- sambaLMPassword
- sambaNTPassword
- sambaPwdLastSet
- sambaLogonTime ----------> no default callback available
- sambaLogoffTime ---------> no default callback available
- sambaKickoffTime --------> no default callback available
- sambaPwdCanChange -------> no default callback available
- sambaPwdMustChange ------> no default callback available
- sambaAcctFlags
- displayName -------------> no default callback available
- sambaHomePath -----------> no default callback available
- sambaHomeDrive ----------> no default callback available
- sambaLogonScript --------> no default callback available
- sambaProfilePath --------> no default callback available
- description -------------> no default callback available
- sambaUserWorkstations ---> no default callback available
- sambaPrimaryGroupSID
- sambaDomainName
- sambaMungedDial ---------> no default callback available
- sambaBadPasswordCount ---> no default callback available
- sambaBadPasswordTime ----> no default callback available
- sambaPasswordHistory ----> no default callback available
- sambaLogonHours ---------> no default callback available


sambaGroupMapping
-----------------

- gidNumber (must)
- sambaSID (must)
- sambaGroupType (must)
- displayName -------------> no default callback available
- description -------------> no default callback available
- sambaSIDList ------------> no default callback available
"""
import smbpasswd
import posix
import time


def sambaNTPassword(passwd):
    return smbpasswd.nthash(passwd)


def sambaLMPassword(passwd):
    return smbpasswd.lmhash(passwd)


# net getlocalsid | net getlocalsid [domain]
SAMBA_LOCAL_SID = 'S-1-5-21-1234567890-1234567890-1234567890'


def sambaUserSID(node, uid):
    """uid * 2 + 1000 = rid for users
    """
    rid = int(posix.uidNumber(None, uid)) * 2 + 1000
    return SAMBA_LOCAL_SID + '-' + str(rid)


SAMBA_DEFAULT_DOMAIN = 'CONE_UGM'


def sambaDomainName(node, uid):
    return SAMBA_DEFAULT_DOMAIN


SAMBA_PRIMARY_GROUP_SID = 'S-1-5-21-1234567890-1234567890-1234567890-123'


def sambaPrimaryGroupSID(node, uid):
    return SAMBA_PRIMARY_GROUP_SID


def sambaPwdLastSet(node, uid):
    return str(int(time.time()))


SAMBA_DEFAULT_ACCOUNT_FLAGS = '[U]'


def sambaAcctFlags(node, uid):
    return SAMBA_DEFAULT_ACCOUNT_FLAGS


def sambaGroupSID(node, uid):
    """gid * 2 + 1001 = rid for groups
    """
    rid = int(posix.gidNumber(None, uid)) * 2 + 1000
    return SAMBA_LOCAL_SID + '-' + str(rid)


SAMBA_DEFAULT_GROUP_TYPE = '2'


def sambaGroupType(node, uid):
    return SAMBA_DEFAULT_GROUP_TYPE
