Test related imports::

    >>> from bda.cache.nullcache import NullCacheManager
    >>> from ldap import MOD_REPLACE
    >>> from node.ext.ldap import BASE
    >>> from node.ext.ldap import LDAPCommunicator
    >>> from node.ext.ldap import LDAPConnector
    >>> from node.ext.ldap import LDAPProps
    >>> from node.ext.ldap import ONELEVEL
    >>> from node.ext.ldap import SUBTREE
    >>> from node.ext.ldap.base import main
    >>> from node.ext.ldap.base import testLDAPConnectivity
    >>> from zope.component import provideAdapter
    >>> import sys

NullCachManager registration::

    >>> provideAdapter(NullCacheManager)

LDAP credentials::

    >>> host = "127.0.0.1"
    >>> port = 12345
    >>> binddn = "cn=Manager,dc=my-domain,dc=com"
    >>> bindpw = "secret"

    >>> props = LDAPProps(
    ...     server=host,
    ...     port=port,
    ...     user=binddn,
    ...     password=bindpw,
    ... )

Test main script, could be used by command line with
'python base.py server port'::

    >>> old_argv = sys.argv
    >>> sys.argv = ['base.py', '127.0.0.1', '12345']
    >>> main()
    success

    >>> sys.argv[-1] = '12346'
    >>> main()
    {'info': 'Transport endpoint is not connected', 
    'errno': 107, 
    'desc': "Can't contact LDAP server"}

    >>> sys.argv = []
    >>> main()
    usage: python base.py [server] [port]

    >>> sys.argv = old_argv

Test node.ext.ldap base objects. Test LDAP connectivity::

    >>> testLDAPConnectivity('127.0.0.1', 12345)
    'success'

    >>> testLDAPConnectivity('127.0.0.1', 12346)
    SERVER_DOWN({'info': 'Transport endpoint is not connected', 
    'errno': 107, 
    'desc': "Can't contact LDAP server"},)

Create connector.::

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
    7

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
    8

Query added entry directly.::

    >>> res = communicator.search('(cn=foo)', SUBTREE)
    >>> res
    [('cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com',
    {'objectClass': ['person', 'top'], 'cn': ['foo'], 'sn': ['bar']})]

Modify this entry and check the result.::

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

    >>> connector = LDAPConnector(props)
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
