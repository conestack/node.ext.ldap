# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

import logging
logger = logging.getLogger('bda.ldap')

try:
    import ldap
except ImportError:
    raise ImportError, u"bda.ldap requires a working python-ldap installation."

from zope.component import queryUtility
from bda.cache import ICacheManager
from bda.ldap.interfaces import ICacheProviderFactory
from bda.ldap.cache import nullcacheProviderFactory

BASE = ldap.SCOPE_BASE
ONELEVEL = ldap.SCOPE_ONELEVEL
SUBTREE = ldap.SCOPE_SUBTREE
SCOPES = [BASE, ONELEVEL, SUBTREE]

def testLDAPConnectivity(server, port):
    """Function to test the availability of the LDAP Server.
    """
    try:
        c = LDAPConnector(server, port, '', '')
        lc = LDAPCommunicator(c)
        lc.bind()
        lc.unbind()
        return 'success'
    except ldap.LDAPError, error:
        return error

def md5digest(key):
    """Needed to support both, python 2.4 and python >=2.5
    
    Will be remove when python 2.4 support is dropped.
    
    XXX: This is maybe expensive. Optimize code eventually.
    """
    try:
        # in python >=2.5
        import hashlib
    except ImportError:
        # fallback if python 2.4
        import md5
        return md5.new(key).hexdigest()
    m = hashlib.md5()
    m.update(key)
    return m.hexdigest()

class LDAPConnector(object):
    """Object is responsible for the LDAP connection.
    
    This Object knows about the LDAP Server to connect to, the authentication
    information and the protocol to use.
    
    TODO: TLS/SSL Support.
    
    Normally you do not need to use this class directly.
        
    >>> c = LDAPConnector('localhost', 389, 'cn=admin,dc=foo,dc=bar', 'secret')
    >>> connection = c.bind()
    >>> # do something with connection
    >>> c.unbind() 
    """
    
    def __init__(self,
                 server,
                 port,
                 bindDN,
                 bindPW,
                 cache=True,
                 cachetimeout=43200):
        """Initialize LDAPConnector.
        
        Signature Deprecated: Signature will take ``LDAPServerProperties``
                              object instead of current kwargs in future.
                              This will be changed in Version 1.5.
        """
        self.protocol = ldap.VERSION3
        self._bindDN = bindDN
        self._server = server
        self._port = port
        self._bindPW = bindPW
        self._cache = cache
        self._cachetimeout = cachetimeout
    
    def setProtocol(self, protocol):
        """Set the LDAP Protocol Version to use.
        
        Deprecated: This function will be removed in version 1.5. Use
                    ``protocol`` property directly instead.
        """
        self.protocol = protocol
    
    def bind(self):
        """Bind to Server and return the Connection Object.
        """
        self._con = ldap.open(self._server, self._port)
        self._con.protocol_version = self.protocol
        self._con.simple_bind(self._bindDN, self._bindPW)
        return self._con
    
    def unbind(self):
        """Unbind from Server.
        """
        self._con.unbind()
        self._con = None

class LDAPCommunicator(object):
    """Class LDAPCommunicator is responsible for the communication with the
    LDAP Server.
    
    It provides methods to search, add, modify and delete entries in the
    directory.
    
    Usage:

    c = LDAPConnector('localhost', 389, 'cn=admin,dc=foo,dc=bar', 'secret')
    lc = LDAPCommunicator(c)
    lc.setBaseDN('ou=customers,dc=foo,dc=bar')
    lc.bind()
    result = lc.search('uid=user@foo.bar', lc.SUBTREE)
    # do soething with result
    ...
    lc.unbind()
    """
    
    def __init__(self, connector):
        """Takes LDAPConnector object as argument.
        """
        self.baseDN = ''
        self._connector = connector
        self._con = None
        self._cache = None
        if connector._cache:
            cachefactory = queryUtility(ICacheProviderFactory)
            if cachefactory is None:
                cachefactory = nullcacheProviderFactory
            cacheprovider = cachefactory()          
            self._cache = ICacheManager(cacheprovider)
            self._cache.setTimeout(connector._cachetimeout)
            logger.debug(u"LDAP Caching activated for instance '%s'. Use '%s' "
                          "as cache provider" % (repr(self._cache),
                                                 repr(cacheprovider)))
        
    def bind(self):
        """Bind to LDAP Server.
        """
        self._con = self._connector.bind()
        
    def unbind(self):
        """Unbind from LDAP Server.
        """
        self._connector.unbind()
        self._con = None
        
    def setBaseDN(self, baseDN):
        """Set the base DN you want to work on.
        
        Deprecated: This function will be removed in version 1.5. Use
                    ``baseDN`` property directly instead.
        """
        self.baseDN = baseDN
        
    def getBaseDN(self):
        """Returns the current set base DN.
        
        Deprecated: This function will be removed in version 1.5. Use
                    ``baseDN`` property directly instead.
        """
        return self.baseDN
        
    def search(self, queryFilter, scope, baseDN=None,
               force_reload=False, attrlist=None, attrsonly=0):
        """Search the directory.
        
        ``queryFilter``
            LDAP query filter
        ``scope``
            LDAP search scope
        ``baseDN``
            Search base. Defaults to ``self.baseDN``
        ``force_reload``
            Force cache to be ignored if enabled.
        ``attrlist``
            LDAP attrlist to query.
        ``attrsonly``
            Flag wether to load DN's (?) only.
        """
        if baseDN is None:
            baseDN = self.baseDN
        if self._cache:
            # XXX: Consider attrlist and attrsonly in cachekey.
            key = '%s-%s-%s-%i' % (self._connector._bindDN,
                                   baseDN,
                                   queryFilter,
                                   scope)
            key = md5digest(key)
            args = [baseDN, scope, queryFilter, attrlist, attrsonly]
            return self._cache.getData(self._con.search_s, key,
                                       force_reload, args)
        return self._con.search_s(baseDN, scope, queryFilter,
                                  attrlist, attrsonly)
    
    def add(self, dn, data):
        """Insert an entry into directory.
        
        Takes the DN of the entry and the data this object contains. data is a
        dict and looks like this:
        
        >>> data = {
        ...     'uid':'foo',
        ...     'givenname':'foo',
        ...     'cn':'foo 0815',
        ...     'sn':'bar',
        ...     'telephonenumber':'123-4567',
        ...     'facsimiletelephonenumber':'987-6543',
        ...     'objectclass':('Remote-Address','person', 'Top'),
        ...     'physicaldeliveryofficename':'Development',
        ...     'mail':'foo@bar.org',
        ...     'title':'programmer',
        ... }
        """
        attributes = [ (k,v) for k,v in data.items() ]
        self._con.add_s(dn, attributes)    
        
    def modify(self, dn, modlist):
        """Modify an existing entry in the directory.
        
        Takes the DN of the entry and the modlist, which is a list of tuples 
        containing modifation descriptions. The first element gives the type 
        of the modification (MOD_REPLACE, MOD_DELETE, or MOD_ADD), the second 
        gives the name of the field to modify, and the third gives the new 
        value for the field (for MOD_ADD and MOD_REPLACE).
        """
        self._con.modify_s(dn, modlist)
        
    def delete(self, deleteDN):
        """Delete an entry from the directory.
        
        Take the DN to delete from the directory as argument.
        """
        self._con.delete_s(deleteDN)

def main():    
    """Use this module from command line for testing the connectivity to the
    LDAP Server.
    
    Expects server and port as arguments.
    """
    import sys
    if len(sys.argv) < 3:
        print 'usage: python base.py [server] [port]'
    else:
        server, port = sys.argv[1:]
        print testLDAPConnectivity(server, int(port))
        
if __name__ == "__main__":
    main()