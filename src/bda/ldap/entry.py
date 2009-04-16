# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

import types
from zodict.node import Node
from bda.ldap import ONELEVEL
from bda.ldap import LDAPSession

from ldap import MOD_ADD
from ldap import MOD_DELETE
from ldap import MOD_REPLACE

ACTION_ADD = 0
ACTION_MODIFY = 1
ACTION_DELETE = 2
ACTION_READ = 3

class LDAPEntry(Node):
    """An LDAP Entry.
    """
    
    def __init__(self, name=None, props=None):
        """The Root entry expects the initial base DN as name and the server
        properties.
        """
        if name and not props or props and not name:
            raise ValueError(u"Wrong initialization.")
        Node.__init__(self, name)
        self._session = None
        if props:
            self._session = LDAPSession(props)
            self._session.setBaseDN(self.DN)
        self.attributes = dict()
        self._orginattrs = dict()
        self._changed = False
        self._action = ACTION_ADD
        self._keys = list()
            
    @property
    def DN(self):
        if not hasattr(self, '_dn'):
            path = self.path
            path.reverse()
            self._dn = ','.join(path)
        return self._dn
    
    def readattrs(self):
        if not self.__parent__:
            # root XXX
            return
        dn = self.__parent__.DN
        entry = self._session.search('(%s)' % self.__name__,
                                     ONELEVEL, baseDN=dn)
        if len(entry) != 1:
            raise RuntimeError(u"Fatal. Expected entry does not exist or "
                                "more than one entry found")
        attrs = entry[0][1]
        for key, item in attrs.items():
            if len(item) == 1:
                attrs[key] = item[0]
        self.attributes.update(attrs)
        self._orginattrs.update(attrs)
    
    def __iter__(self):
        if not self._keys:
            children = self._session.search('(objectClass=*)', ONELEVEL,
                                            baseDN=self.DN, attrsonly=1)
            for dn, attrs in children:
                self._keys.append(dn[:dn.rfind(self.DN)].strip(','))
        for key in self._keys:
            yield key
    
    iterkeys = __iter__
    
    def __getitem__(self, key):
        if not key in self.keys():
            raise KeyError(u"Entry not existent: %s" % key)
        try:
            child = Node.__getitem__(self, key)
        except KeyError, e:
            child = LDAPEntry()
            child._action = ACTION_READ
            self[key] = child
        return child
    
    def __setitem__(self, key, val):
        try:
            self._keys.remove(key)
        except ValueError, e: pass
        val._session = self._session
        if key in self.keys():
            val._changed = True
            val._action = ACTION_MODIFY
        Node.__setitem__(self, key, val)
        self._keys.append(key)
        if val._action == ACTION_READ:
            val.readattrs()
            val._action = None
        else:
            val._changed = True
            val._action = ACTION_ADD
        self._changed = True
    
    def __delitem__(self, key):
        """Do not delete immediately. Just mark Entry to be deleted and
        remove key from self._keys.
        """
        todelete = self[key]
        todelete._changed = True
        todelete._action = ACTION_DELETE
        self._keys.remove(key)
    
    def __call__(self):
        for entry in Node.values(self):
            entry()
        self._checkattrchanged()
        if not self._changed:
            return
        action = self._action
        if action == ACTION_ADD:
            self._add()
        if action == ACTION_MODIFY:
            self._modify()
        if action == ACTION_DELETE:
            self._delete()
    
    def _checkattrchanged(self):
        if len(self.attributes) != len(self._orginattrs):
            self._changed = True
            return
        for key in self.attributes.keys():
            if self.attributes[key] != self._orginattrs[key]:
                self._changed = True
                return
    
    def _add(self):
        print 'add'
        self._session.add(self.DN, self.attributes)
    
    def _modify(self):
        print 'modify'
        modlist = list()
        orginkeys = self._orginattrs.keys()
        attrkeys = self.attributes.keys()
        for key in orginkeys:
            # MOD_DELETE
            if not key in attrkeys:
                moddef = (MOD_DELETE, key, None)
                modlist.append(moddef)
        for key in attrkeys:
            # MOD_ADD
            if not key in orginkeys:
                moddef = (MOD_ADD, key, self.attributes[key])
                modlist.append(moddef)
            # MOD_REPLACE
            if key in orginkeys:
                if self.attributes[key] != self._orginattrs[key]:
                    moddef = (MOD_REPLACE, key, self.attributes[key])
                    modlist.append(moddef)
        if modlist:
            self._session.modify(self.DN, modlist)
    
    def _delete(self):
        print 'delete'
        self.session.delete(self.DN)
        Node.__delitem__(self.__parent__, self.__name__)