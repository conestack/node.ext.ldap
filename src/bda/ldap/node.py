# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

import types
import copy
from odict import odict
from zope.interface import implements
try:
    from zope.app.event.objectevent import objectEventNotify # BBB
except ImportError, e:
    from zope.component.event import objectEventNotify
from zodict.interfaces import ICallableNode
from zodict import LifecycleNode
from zodict.node import NodeAttributes
from bda.ldap import (
    ONELEVEL,
    LDAPSession,
)
from bda.ldap.strcodec import encode, decode
from ldap.functions import explode_dn
from ldap import (
    MOD_ADD,
    MOD_DELETE,
    MOD_REPLACE,
)

ACTION_ADD = 0
ACTION_MODIFY = 1
ACTION_DELETE = 2

def queryNode(props, dn):
    """Query an ldap entry and return as LDAPNode.
    
    ``props``
        ``LDAPProps`` instance
    ``dn``
        DN of the node to query
    """
    containerdn = ','.join(explode_dn(dn)[1:])
    nodedn = explode_dn(dn)[0]
    container = LDAPNode(name=containerdn, props=props)
    return container.get(nodedn, None)

class LDAPNodeAttributes(NodeAttributes):
    
    def __init__(self, node):
        super(LDAPNodeAttributes, self).__init__(node)
        self.load()

    def load(self):
        if self._node.__parent__ is None or self._node._action == ACTION_ADD:
            return
        self.clear()
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
        self.changed = False
        if self._node._action not in [ACTION_ADD, ACTION_DELETE]:
            self._node._action = None
            self._node.changed = False
                
    def __setitem__(self, key, val):
        if isinstance(key, str):
            key = decode(key)
        if isinstance(val, str):
            val = decode(val)
        super(LDAPNodeAttributes, self).__setitem__(key, val)
        self._set_attrs_modified()
    
    def __delitem__(self, key):
        if isinstance(key, str):
            key = decode(key)
        super(LDAPNodeAttributes, self).__delitem__(key)
        self._set_attrs_modified()
    
    def __getattribute__(self, name):
        # XXX: why is that necessary?
        return object.__getattribute__(self, name)
    
    def __setattr__(self, name, value):
        # XXX: why is that necessary?
        object.__setattr__(self, name, value)
    
    def _set_attrs_modified(self):
        if self._node._action not in [ACTION_ADD, ACTION_DELETE]:
            self._node._action = ACTION_MODIFY
            self._node.changed = True

class LDAPNode(LifecycleNode):
    """An LDAP Node.
    """
    implements(ICallableNode)
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
        if name and not isinstance(name, unicode):
            name = name.decode(props.encoding)
        self.__name__ = name
        self._session = None        
        self._changed = False
        self._action = None
        # the _keys is None or an odict.
        # if an odict, the value is either None or the value
        # None means, the value wasnt loaded 
        self._keys = None 
        self._reload = False        
        if props:
            self._session = LDAPSession(props)
            self._session.baseDN = self.DN
        super(LDAPNode, self).__init__(name)
            
    @property
    def DN(self):
        if not hasattr(self, '_dn'):
            self._dn = ','.join(reversed(self.path))
        return self._dn                  
    
    def __iter__(self):
        """This is where keys are retrieved from ldap
        """
        if self.__name__ is None:
            return
        if self._reload:
            self._keys = None        
        if self._keys is None and self._action != ACTION_ADD:
            self._keys = odict()
            children = self._session.search('(objectClass=*)',
                                            ONELEVEL,
                                            baseDN=self.DN,
                                            force_reload=self._reload,
                                            attrsonly=1)
            for dn, attrs in children:
                # explode_dn is ldap world
                key = decode(explode_dn(encode(dn))[0])
                self._keys[key] = None
            for key in self._keys:
                yield key
        elif self._keys:        
            for key in self._keys:
                yield key
    
    iterkeys = __iter__
    
    def iteritems(self):
        for key in self:
            yield key, self[key]

    def sort(self, cmp=None, key=None, reverse=False):
        # XXX: a sort working only on the keys could work without wakeup -->
        # sortonkeys()
        #  first wake up all entries 
        dummy = self.items()
        if not dummy:
            return
        # second sort them
        self._keys.sort(cmp=cmp, key=key, reverse=reverse)
    
    def __getitem__(self, key):
        """Here nodes are created for keys, iff they do not exist already
        """
        if isinstance(key, str):
            key = decode(key)
        if not key in self:
            raise KeyError(u"Entry not existent: %s" % key)
        if self._keys[key] is not None:
            return super(LDAPNode, self).__getitem__(key)
        val = LDAPNode()
        val._session = self._session
        self._notify_suppress = True
        super(LDAPNode, self).__setitem__(key, val)
        self._notify_suppress = False
        self._keys[key] = val
        return val

    def get(self, key, default=None):
        """Otherwise odict/pyodicts __getitem__ is used...

        XXX: Maybe this could be higher up in the hierarchy
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, val):
        if isinstance(key, str):
            key = decode(key)
        val._session = self._session
        if self._keys is None:
            self._keys = odict()
        try:
            # a value with key is already in the directory
            self._keys[key]
        except KeyError, e:
            # the value is not yet in the directory 
            val._action = ACTION_ADD
            val.changed = True
            self.changed = True 
        self._notify_suppress = True
        super(LDAPNode, self).__setitem__(key, val)
        self._notify_suppress = False
        self._keys[key] = val    
        if val._action == ACTION_ADD:
            objectEventNotify(self.events['added'](val, newParent=self, 
                                                   newName=key))
    
    def __delitem__(self, key):
        """Do not delete immediately. Just mark LDAPNode to be deleted and
        remove key from self._keys.
        """
        if isinstance(key, str):
            key = decode(key)
        val = self[key]
        val.changed = True
        val._action = ACTION_DELETE
        del self._keys[key]
        if not hasattr(self, '_deleted'):
            self._deleted = list()
        self._deleted.append(val) 
        self.changed = True
    
    def __call__(self):
        if self.changed and self._action is not None:
            if self._action == ACTION_ADD:
                self._ldap_add()
            elif self._action == ACTION_MODIFY:
                self._ldap_modify()
            elif self._action == ACTION_DELETE:
                self._ldap_delete()
            if hasattr(self, '_attributes'):
                self.attributes.changed = False
            self.changed = False
            self._action = None                    
        if self._keys is None:
            return
        for node in self._keys.values() + getattr(self, '_deleted', []):
            if node is not None and node.changed:
                node()
    
    def __repr__(self):
        if self.__parent__ is None:
            return "<%s - %s>" % (self.DN, self.changed)
        return "<%s:%s - %s>" % (self.DN, self.__name__, self.changed)
    
    __str__ = __repr__
    
    @property
    def noderepr(self):
        return repr(self)
    
    def _ldap_add(self):
        """adds self to the ldap directory.
        """
        self._session.add(self.DN, self.attributes)
    
    def _ldap_modify(self):
        """modifies attributs of self on the ldap directory.
        """ 
        modlist = list()
        orgin = self.attributes_factory(self)
        for key in orgin:
            # MOD_DELETE
            if not key in self.attributes:
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
    
    def _ldap_delete(self):
        """delete self from the ldap-directory.
        """
        self.__parent__._keys[self.__name__] = None
        super(LifecycleNode, self.__parent__).__delitem__(self.__name__)
        del self.__parent__._keys[self.__name__]
        self._session.delete(self.DN)
    
    def _get_changed(self):
        return self._changed

    def _set_changed(self, value):
        self._changed = value
        if self.__parent__ is None:
            return
        if not value and self.__parent__.changed:
            # check parents loaded children if one of them is changed
            # if so, keep parent marked as changed
            siblings = list()
            if self._keys:
                siblings = [v for v in self._keys.values() if v is not None]
            siblings += getattr(self, '_deleted', [])
            for sibling in siblings:
                if sibling is self:
                    continue
                if sibling.changed:
                    return
            self.__parent__.changed = value
        elif value and not self.__parent__.changed:
            self.__parent__.changed = value                
            
    changed = property(_get_changed, _set_changed) 
    
    @property
    def ldap_session(self):
        return self._session
