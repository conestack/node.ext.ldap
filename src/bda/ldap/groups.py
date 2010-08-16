from zope.interface import implements
from bda.ldap import LDAPProps, LDAPNode
from bda.ldap import BASE, ONELEVEL, SUBTREE
from bda.ldap.interfaces import ILDAPGroupsConfig
from bda.ldap.users import LDAPPrincipal, LDAPPrincipals, LDAPPrincipalsConfig
  
def EventHandler(event):
  """handle for emmited events
  """
  
  

class LDAPGroupsConfig(LDAPPrincipalsConfig):
    """Define how groups look and where they are
    """
    implements(ILDAPGroupsConfig)
    

class LDAPGroup(LDAPPrincipal):
    """An LDAP group

        for groups children are found by:
        - we have a multivalue attribute pointing to member dns
        - has an attribute pointing to our dn
        - we have an attribute that matches another attribute on the user

        AD: dn:memberOf
        openldap: member:dn
        posix: memberUid:uidNumber|gidNumber:gidNumber
        arbitrary: group_attr:user_attr  |   &    ()
    """

class LDAPGroups(LDAPPrincipals):
    """Manage LDAP groups 
    """
    def __init__(self, cfg):
        super(LDAPGroups, self).__init__(cfg)
        self._ChildClass = LDAPGroup
