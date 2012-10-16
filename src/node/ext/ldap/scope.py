# -*- coding: utf-8 -*-
import ldap

BASE = ldap.SCOPE_BASE
ONELEVEL = ldap.SCOPE_ONELEVEL
SUBTREE = ldap.SCOPE_SUBTREE
SCOPES = [BASE, ONELEVEL, SUBTREE]

del ldap
