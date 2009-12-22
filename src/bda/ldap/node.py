# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

import types
import copy
from zope.component.event import objectEventNotify
from zodict import LifecycleNode
from zodict.node import NodeAttributes
from bda.ldap import ONELEVEL
from bda.ldap import LDAPSession

from ldap import MOD_ADD
from ldap import MOD_DELETE
from ldap import MOD_REPLACE

ACTION_ADD = 0
ACTION_MODIFY = 1
ACTION_DELETE = 2

def queryNode(props, dn):
    """Query an ldap entry and return as LDAPNode.
    
    @param props: LDAPServerPropertier instance
    @param dn: DN of the node to query
    @return: Node instance or None if inexistent 
    """
    containerdn = dn[dn.find(',') + 1:]
    nodedn = dn[:dn.find(',')]
    container = LDAPNode(name=containerdn, props=props)
    return container.get(nodedn, None)

class LDAPNodeAttributes(NodeAttributes):
    
    def __init__(self, node):
        super(LDAPNodeAttributes, self).__init__(node)
        self.load()
        self.changed = False
    
    def load(self):
        self.clear()
        if self._node.__parent__ is None:
            return
        dn = self._node.__parent__.DN
        search = self._node._session.search
        entry = search('(%s)' % self._node.__name__, ONELEVEL, baseDN=dn,
                       force_reload=self._node._reload)        
        if len(entry) != 1:
            raise RuntimeError(u"Fatal. Expected entry does not exist or "
                                "more than one entry found")
        attrs = entry[0][1]
        for key, item in attrs.items():
            if len(item) == 1:
                self[key] = item[0]
            else:
                self[key] = item
                
    def __setitem__(self, key, val):
        super(LDAPNodeAttributes, self).__setitem__(key, val)
        if self._node._action not in [ACTION_ADD, ACTION_DELETE]:
            self._node._action = ACTION_MODIFY            

class LDAPNode(LifecycleNode):
    """An LDAP Node.
    """
    
    attributes_factory = LDAPNodeAttributes
    
    def __init__(self, name=None, props=None):
        """LDAP Node expects both, ``name`` and ``props`` arguments for the 
        root LDAP Node or nothing for children as parameters. 
        
        ``name`` 
            Initial base DN for the root LDAP Node.
        
        ``props`` 
            ``bda.ldap.LDAPProperties`` object.
        """
        if (name and not props) or (props and not name):
            raise ValueError(u"Wrong initialization.")
        self.__name__ = name
        self._session = None        
        self._changed = False
        self._action = None
        self._keys = None
        self._reload = False        
        if props:
            self._session = LDAPSession(props)
            self._session.setBaseDN(self.DN)                
        super(LDAPNode, self).__init__(name)
            
    @property
    def DN(self):
        if not hasattr(self, '_dn'):
            self._dn = ','.join(reversed(self.path))
        return self._dn                  
    
    def __iter__(self):
        if self.__name__ is None:
            return
        if self._reload:
            self._keys = None        
        if self._keys is None:
            self._keys = list()
            children = self._session.search('(objectClass=*)',
                                            ONELEVEL,
                                            baseDN=self.DN,
                                            force_reload=self._reload,
                                            attrsonly=1)
            for dn, attrs in children:
                key = dn[:dn.rfind(self.DN)].strip(',')
                self._keys.append(key)
                yield key
        else:        
            for key in self._keys:
                yield key
    
    iterkeys = __iter__
    
    def __getitem__(self, key):
        if not key in self:
            raise KeyError(u"Entry not existent: %s" % key)
        try:
            child = super(LDAPNode, self).__getitem__(key)
        except KeyError, e:
            child = LDAPNode()
            self[key] = child
        return child
    
    def __setitem__(self, key, val):
        val._session = self._session
        try:
            self._keys.remove(key)
        except ValueError, e:
            val._action = ACTION_ADD
            self._changed = True
        self._notify_suppress = True
        super(LDAPNode, self).__setitem__(key, val)
        self._notify_suppress = False
        self._keys.append(key)    
        if val._action == ACTION_ADD:
            objectEventNotify(self.events['added'](val, newParent=self, 
                                                   newName=key))
    
    def __delitem__(self, key):
        """Do not delete immediately. Just mark LDAPNode to be deleted and
        remove key from self._keys.
        """
        val = self[key]
        val._changed = True
        val._action = ACTION_DELETE
        self._keys.remove(key)
        self._changed = True
    
    def __call__(self):
        if self._changed:
            if self._action == ACTION_ADD:
                self._ldap_add()
            elif self._action == ACTION_MODIFY:
                self._ldap_modify()
            elif self._action == ACTION_DELETE:
                self._ldap_delete()
        for node in super(LDAPNode, self).values():
            node()
    
    def _checkattrchanged(self):
        if self._action == ACTION_ADD:
            return
        
        if len(self.attributes) != len(self._orginattrs):
            curattrs = copy.copy(self.attributes)
            self._reload = True
            self.readattrs()
            self._reload = False
            self.attributes = curattrs
            if len(self.attributes) != len(self._orginattrs):
                self._changed = True
                self._action = ACTION_MODIFY
                return
        for key in self.attributes.keys():
            if self.attributes[key] != self._orginattrs[key]:
                self._changed = True
                self._action = ACTION_MODIFY
                return
    
    def _ldap_add(self):
        """adds self to the ldap directory.
        """
        self._session.add(self.DN, self.attributes)
        self._changed = False
        self._action = None
    
    def _ldap_modify(self):
        """modifies attributs of self on the ldap directory.
        """ 
        modlist = list()
        orgin = self.attributes_factory(self)
        for key in orgin:
            # MOD_DELETE
            if not key in attrkeys:
                moddef = (MOD_DELETE, key, None)
                modlist.append(moddef)
        for key in self.attributes:
            # MOD_ADD
            if key not in orgin:
                moddef = (MOD_ADD, key, self.attributes[key])
                modlist.append(moddef)
            # MOD_REPLACE
            elif self.attributes[key] != orgin[key]:
                moddef = (MOD_REPLACE, key, self.attributes[key])
                modlist.append(moddef)
        if modlist:
            self._session.modify(self.DN, modlist)
        self._changed = False
        self._action = None
    
    def _ldap_delete(self):
        """delete self from the ldap-directory.
        
        the key was already kicked by self.__delitem__ to keep state sane.
        we might want to add another property to this object keeping the
        deleted keys to avoid reloading the keys from the directory.
        """
        self._session.delete(self.DN)
        super(LDAPNode, self).__delitem__(self.__parent__, self.__name__)