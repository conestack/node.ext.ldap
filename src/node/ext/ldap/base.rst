LDAP credentials.::

    >>> host = "127.0.0.1"
    >>> port = 12345
    >>> binddn = "cn=Manager,dc=my-domain,dc=com"
    >>> bindpw = "secret"
    
    >>> from node.ext.ldap import LDAPProps
    >>> props = LDAPProps(
    ...     server=host,
    ...     port=port,
    ...     user=binddn,
    ...     password=bindpw,
    ... )

Test main script, could be used by command line with
'python base.py server port'::

    >>> from node.ext.ldap.base import main
    >>> import sys
    >>> old_argv = sys.argv
    >>> sys.argv = ['base.py', '127.0.0.1', '12345']
    >>> main()
    success
    
    >>> sys.argv[-1] = '12346'
    >>> main()
    {'desc': "Can't contact LDAP server"}
    
    >>> sys.argv = []
    >>> main()
    usage: python base.py [server] [port]
    
    >>> sys.argv = old_argv

Test node.ext.ldap base objects.::

    >>> from node.ext.ldap import BASE, ONELEVEL, SUBTREE
    >>> from node.ext.ldap import LDAPConnector
    >>> from node.ext.ldap import LDAPCommunicator

Test LDAP connectivity::

    >>> from node.ext.ldap.base import testLDAPConnectivity
    >>> testLDAPConnectivity('127.0.0.1', 12345)
    'success'
    
    >>> testLDAPConnectivity('127.0.0.1', 12346)
    SERVER_DOWN({'desc': "Can't contact LDAP server"},)

Create connector.

Old signature. To be remove in 1.0::

    >>> connector = LDAPConnector(host, port, binddn, bindpw, cache=False)
    >>> connector
    <node.ext.ldap.base.LDAPConnector object at ...>

New signature, use this one::

    >>> connector = LDAPConnector(props=props)
    >>> connector
    <node.ext.ldap.base.LDAPConnector object at ...>

Create communicator.::

    >>> communicator = LDAPCommunicator(connector)
    >>> communicator
    <node.ext.ldap.base.LDAPCommunicator object at ...>

Bind to directory.::

    >>> communicator.bind()

Search fails if baseDN is not set and not given to search function::

    >>> communicator.baseDN
    ''
    
    >>> res = communicator.search('(objectClass=*)', SUBTREE)
    Traceback (most recent call last):
      ...
    ValueError: baseDN unset.

Set base dn and check if previously imported entries are present.::

    >>> communicator.baseDN = 'dc=my-domain,dc=com'
    >>> res = communicator.search('(objectClass=*)', SUBTREE)
    >>> len(res)
    6
  
Test inserting entries.::

    >>> entry = {
    ...     'cn':'foo',
    ...     'sn':'bar',
    ...     'objectclass':('person', 'top'),
    ... }
    >>> dn = 'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com'
    >>> communicator.add(dn, entry)

Now there's one more entry in the directory.::

    >>> res = communicator.search('(objectClass=*)', SUBTREE)
    >>> len(res)
    7

Query added entry directly.::

    >>> res = communicator.search('(cn=foo)', SUBTREE)
    >>> res
    [('cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com', 
    {'objectClass': ['person', 'top'], 'cn': ['foo'], 'sn': ['bar']})]

Modify this entry and check the result.::

    >>> from ldap import MOD_REPLACE
    >>> communicator.modify(res[0][0], [(MOD_REPLACE, 'sn', 'baz')])
    >>> res = communicator.search('(cn=foo)', SUBTREE)
    >>> res
    [('cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com', 
    {'objectClass': ['person', 'top'], 'cn': ['foo'], 'sn': ['baz']})]

Finally delete this entry and check the result.::

    >>> communicator.delete(res[0][0])
    >>> communicator.search('(cn=foo)', SUBTREE)
    []

Unbind from server.::

    >>> communicator.unbind()

Connector using cache.::
    
    >>> connector = LDAPConnector(host, port, binddn, bindpw)
    >>> communicator = LDAPCommunicator(connector)
    >>> communicator.bind()

Add entry::
    
    >>> entry = {
    ...     'cn':'foo',
    ...     'sn':'bar',
    ...     'objectclass':('person', 'top'),
    ... }
    >>> dn = 'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com'
    >>> communicator.add(dn, entry)
    >>> communicator.baseDN = 'dc=my-domain,dc=com'

Search cached entry. Does not get cached here since no real cache provider is
registered. Thus the nullcacheProviderFactory is used. But cache API is used
anyways::

    >>> res = communicator.search('(cn=foo)', SUBTREE)
    >>> res
    [('cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com', 
    {'objectClass': ['person', 'top'], 'cn': ['foo'], 'sn': ['bar']})]

Delete entry::

    >>> communicator.delete(res[0][0])
    >>> res = communicator.search('(cn=foo)', SUBTREE, force_reload=True)
    >>> res
    []
    
    >>> communicator.unbind()
    
TODO:
-----

AD escaping, question -> gogo

from PASGroupsFromLDAP

    #---------------------------------------------------------------------------
    # helper methods
    def escapeValue(self, query):
        """ Escapes a query, note that this is documented for AD queries, but
            not for OpenLDAP etc; But hopefully they work in the same manner.
        """
        config = self.getConfig()
        if not config['escapevalues']:
            return query
        replacements = {'(' :'\\28',
                        ')' :'\\29',
                        '\\':'\\5c',
                        '/' :'\\2f',
                        }
                        # don't know how to 'find' NUL = \\0
                        #'*' :'\\2a',
        for key, value in replacements.items():
            query = query.replace(key, value)
        return query