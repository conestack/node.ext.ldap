# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

from zodict.node import Node
from bda.ldap import ONELEVEL
from bda.ldap import LDAPSession

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
        self.attributes.update(entry[0][1])
    
    def __iter__(self):
        if not hasattr(self, '_keys'):
            self._keys = list()
            children = self._session.search('(objectClass=*)', ONELEVEL,
                                            attrsonly=1)
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
            self[key] = child
        return child
    
    def __setitem__(self, key, val):
        self._keys.remove(key)
        val._session = self._session
        Node.__setitem__(self, key, val)
        self._keys.append(key)
        val.readattrs()