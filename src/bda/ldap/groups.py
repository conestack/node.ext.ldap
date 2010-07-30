from zope.interface import implements
from bda.ldap import LDAPProps, LDAPNode
from bda.ldap import BASE, ONELEVEL, SUBTREE
from bda.ldap.interfaces import ILDAPGroupsConfig
from bda.ldap.users import LDAPPrincipal, LDAPPrincipals
  
def EventHandler(event):
  """handle for emmited events
  """
  
  

class LDAPGroupsConfig(object):
    """Define how groups look and where they are
    """
    implements(ILDAPGroupsConfig)
    
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
    """An LDAP group, it checks compatobility with LDAP
    """
  def __init__ (self, principalSet = None):
        zope.component.provideHandler(self._handler)
	if userset:
	  self._pSet = set(principalSet)
	else:
	  self._pSet = set()
	
  def _handler(self,event):
	""" events regarding principals are passed here as soon as they happen
	"""
    
  def add(self,LDAPPrincipal):
    """Add the user/group to a set and subscribe to signals the user sends
    """
  
  def remove_user(self, LDAPPrincipal):
    """Removes a user/group from the group
    """
    
  def update(self):
    """Updates the group from the server
    """
    
  def __call__():
    """Commits changes made
    """

class LDAPGroups(LDAPPrincipals):
    """Manage LDAP groups 
    """
    def __init__(self, cfg):
        super(LDAPGroups, self).__init__(cfg)
        self._ChildClass = LDAPGroup
    
	