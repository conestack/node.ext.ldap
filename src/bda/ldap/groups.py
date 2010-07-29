from bda.ldap import LDAPProps, LDAPNode
from bda.ldap import BASE, ONELEVEL, SUBTREE
from bda.ldap.users import LDAPPrincipal, LDAPPrincipals

class LDAPGroupsConfig(object):
    """Define how users look and where they are
    """
    def __init__(self,
            props,
            baseDN='',
            id_attr='cn',
            scope=ONELEVEL,
            queryFilter='(objectClass=groupOfNames)'):
        self.props = props
        self.baseDN = baseDN
        self.id_attr = id_attr
        self.scope = scope
        self.queryFilter = queryFilter

class LDAPGroup(LDAPPrincipal):
    """An LDAP group :D
    """

class LDAPGroups(LDAPPrincipals):
    """Manage LDAP groups
    """
    def __init__(self, cfg):
        super(LDAPGroups, self).__init__(cfg)
        self._ChildClass = LDAPGroup
