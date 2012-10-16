# -*- coding: utf-8 -*-
"""
shadowAccount
-------------

- uid (must)
- userPassword -----> no default callback available
- shadowLastChange
    The number of days (since January 1, 1970) since the password was last
    changed.
    NOT CONSIDERED
- shadowMin
    The number of days before password may be changed (0 indicates it may be
    changed at any time)
    NOT CONSIDERED
- shadowMax
    The number of days after which password must be changed (99999 indicates
    user can keep his or her password unchanged for many, many years)
    NOT CONSIDERED
- shadowWarning
    The number of days to warn user of an expiring password (7 for a full week)
    NOT CONSIDERED
- shadowInactive
    The number of days after password expires that account is disabled
    CONSIDERED
- shadowExpire
    The number of days since January 1, 1970 that an account has been disabled
    CONSIDERED
- shadowFlag
    A reserved field for possible future use
    NOT CONSIDERED
- description ------> no default callback available
"""


SHADOW_DEFAULT_FLAG = '0'


def shadowFlag(node, uid):
    return SHADOW_DEFAULT_FLAG


SHADOW_DEFAULT_MIN = '0'


def shadowMin(node, uid):
    return SHADOW_DEFAULT_MIN


SHADOW_DEFAULT_MAX = '99999'


def shadowMax(node, uid):
    return SHADOW_DEFAULT_MAX


SHADOW_DEFAULT_WARNING = '0'


def shadowWarning(node, uid):
    return SHADOW_DEFAULT_WARNING


SHADOW_DEFAULT_INACTIVE = '0'


def shadowInactive(node, uid):
    return SHADOW_DEFAULT_INACTIVE


def shadowLastChange(node, uid):
    # XXX: compute.
    return '12011'


SHADOW_DEFAULT_EXPIRE = '99999'


def shadowExpire(node, uid):
    return SHADOW_DEFAULT_EXPIRE
