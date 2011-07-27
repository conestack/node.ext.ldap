Overview
========

``node.ext.ldap`` is a LDAP convenience library for LDAP communication based on 
`python-ldap <http://pypi.python.org/pypi/python-ldap>`_ and
`node <http://pypi.python.org/pypi/node>`_.

The package contains base configuration and communication objects, a LDAP node
object and a LDAP node based user and group management implementation utilizing
`node.ext.ugm <http://pypi.python.org/pypi/node.ext.ugm>`_.

.. _`RFC 2251`: http://www.ietf.org/rfc/rfc2251.txt

This package is the successor of 
`bda.ldap <http://pypi.python.org/pypi/bda.ldap>`_.


Usage
=====

LDAP Properties
---------------

To define connectivity properties for LDAP use ``node.ext.ldap.LDAPProps``
object.::

    >>> from node.ext.ldap import LDAPProps    
    >>> props = LDAPProps(uri='ldap://localhost:12345/',
    ...                   user='cn=Manager,dc=my-domain,dc=com',
    ...                   password='secret',
    ...                   cache=False)

Test server connectivity with ``node.ext.ldap.testLDAPConnectivity``.::

    >>> from node.ext.ldap import testLDAPConnectivity
    >>> testLDAPConnectivity(props=props)
    'success'


LDAP Connection
---------------

For handling LDAP connections, ``node.ext.ldap.LDAPConnector`` is used. It
expects a ``LDAPProps`` instance in the constructor. Normally there is no
need to instantiate this object directly, this happens during creation of
higher abstractions, see below.::

    >>> from node.ext.ldap import LDAPConnector
    >>> connector = LDAPConnector(props=props)
    >>> connector
    <node.ext.ldap.base.LDAPConnector object at ...>

Calling ``bind`` creates and returns the LDAP connection.::

    >>> connector.bind()
    <ldap.ldapobject.SimpleLDAPObject instance at ...>

Calling ``unbind`` destroys the connection.::

    >>> connector.unbind()


LDAP Communication
------------------

For communicating with an LDAP server, ``node.ext.ldap.LDAPCommunicator`` is
used. It provides all the basic functions needed to search and modify the
directory.

``LDAPCommunicator`` expects a ``LDAPConnector`` instance at creation time.::

    >>> from node.ext.ldap import LDAPCommunicator
    >>> communicator = LDAPCommunicator(connector)
    >>> communicator
    <node.ext.ldap.base.LDAPCommunicator object at ...>

Bind to server.::

    >>> communicator.bind()

Adding directory entry.::

    >>> communicator.add(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     {
    ...         'cn': 'foo',
    ...         'sn': 'Mustermann',
    ...         'userPassword': 'secret',
    ...         'objectClass': ['person'],
    ...     })

Set default search DN.::

    >>> communicator.baseDN = 'ou=demo,dc=my-domain,dc=com'

Search in directory.::

    >>> import node.ext.ldap
    >>> communicator.search('(objectClass=person)', node.ext.ldap.SUBTREE)
    [('cn=foo,ou=demo,dc=my-domain,dc=com', 
    {'objectClass': ['person'], 
    'userPassword': ['secret'], 
    'cn': ['foo'], 
    'sn': ['Mustermann']})]

Modify directory entry.::

    >>> from ldap import MOD_REPLACE
    >>> communicator.modify('cn=foo,ou=demo,dc=my-domain,dc=com',
    ...                     [(MOD_REPLACE, 'sn', 'Musterfrau')])
    
    >>> communicator.search('(objectClass=person)',
    ...                     node.ext.ldap.SUBTREE,
    ...                     attrlist=['cn'])
    [('cn=foo,ou=demo,dc=my-domain,dc=com', 
    {'cn': ['foo']})]

Change the password of a directory entry which represents a user.::

    >>> communicator.passwd(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com', 'secret', '12345')
    
    >>> communicator.search('(objectClass=person)',
    ...                     node.ext.ldap.SUBTREE,
    ...                     attrlist=['userPassword'])
    [('cn=foo,ou=demo,dc=my-domain,dc=com', 
    {'userPassword': ['{SSHA}...']})]

Delete directory entry.::

    >>> communicator.delete('cn=foo,ou=demo,dc=my-domain,dc=com')
    
    >>> communicator.search('(objectClass=person)', node.ext.ldap.SUBTREE)
    []

Close connection.::

    >>> communicator.unbind()


LDAP Session
------------

A more convenient way for dealing with LDAP is provided by
``node.ext.ldap.LDAPSession``. It basically provides the same functionality
as ``LDAPCommunicator``, but automatically creates the connectivity objects
and checks the connection state before performing actions.

Instantiate ``LDAPSession`` object. Expects ``LDAPProps`` instance.::

    >>> from node.ext.ldap import LDAPSession
    >>> session = LDAPSession(props)

LDAP session has a convenience to check given properties.::

    >>> session.checkServerProperties()
    (True, 'OK')

Set default search DN for session.::

    >>> session.baseDN = 'ou=demo,dc=my-domain,dc=com'

Search in directory.::

    >>> session.search()
    [(u'ou=demo,dc=my-domain,dc=com', 
    {u'objectClass': [u'top', u'organizationalUnit'], 
    u'ou': [u'demo'], 
    u'description': [u'Demo organizational unit']})]

Add directory entry.::

    >>> session.add(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     {
    ...         'cn': 'foo',
    ...         'sn': 'Mustermann',
    ...         'userPassword': 'secret',
    ...         'objectClass': ['person'],
    ...     })

Change the password of a directory entry which represents a user.::

    >>> session.passwd('cn=foo,ou=demo,dc=my-domain,dc=com', 'secret', '12345')

Authenticate a specific user.::

    >>> session.authenticate('cn=foo,ou=demo,dc=my-domain,dc=com', '12345')
    True

Modify directory entry.::
    
    >>> session.modify('cn=foo,ou=demo,dc=my-domain,dc=com',
    ...                [(MOD_REPLACE, 'sn', 'Musterfrau')])
    
    >>> session.search('(objectClass=person)',
    ...                node.ext.ldap.SUBTREE,
    ...                attrlist=['cn'])
    [(u'cn=foo,ou=demo,dc=my-domain,dc=com', {u'cn': [u'foo']})]

Delete directory entry.::

    >>> session.delete('cn=foo,ou=demo,dc=my-domain,dc=com')
    >>> session.search('(objectClass=person)', node.ext.ldap.SUBTREE)
    []

Close session.::

    >>> session.unbind()


LDAP Nodes
----------

One can deal with LDAP entries as node objects. Therefor
``node.ext.ldap.LDAPNode`` is used. To get a clue of the complete
node API, see `node <http://pypi.python.org/pypi/node>`_ package.

Create a LDAP node. The root Node expects the base DN and a ``LDAPProps``
instance.::

    >>> from node.ext.ldap import LDAPNode
    >>> root = LDAPNode('ou=demo,dc=my-domain,dc=com', props=props)

Every LDAP node has a DN and a RDN.::

    >>> root.DN
    u'ou=demo,dc=my-domain,dc=com'
    
    >>> root.rdn_attr
    u'ou'

Directory entry has no children yet.::

    >>> root.keys()
    []
    
Add children to root node.::

    >>> person = LDAPNode()
    >>> person.attrs['objectClass'] = ['person']
    >>> person.attrs['sn'] = 'Mustermann'
    >>> person.attrs['userPassword'] = 'secret'
    >>> root['cn=person1'] = person
    
    >>> person = LDAPNode()
    >>> person.attrs['objectClass'] = ['person']
    >>> person.attrs['sn'] = 'Musterfrau'
    >>> person.attrs['userPassword'] = 'secret'
    >>> root['cn=person2'] = person

If the RDN attribute was not set during node creation, it is computed from
node key and set automatically.::

    >>> person.attrs['cn']
    u'person2'

Some might fetch children DN's by key from LDAP node. This only works for
existing children::

    >>> root.child_dn('cn=person1')
    u'cn=person1,ou=demo,dc=my-domain,dc=com'
    
    >>> root.child_dn('cn=person99')
    Traceback (most recent call last):
      ...
    KeyError: 'cn=person99'

Have a look at the tree.::

    >>> root.printtree()
    <ou=demo,dc=my-domain,dc=com - True>
      <cn=person1,ou=demo,dc=my-domain,dc=com:cn=person1 - True>
      <cn=person2,ou=demo,dc=my-domain,dc=com:cn=person2 - True>

The entries have not been written to the directory yet. When modifying a LDAP
node tree, everything happens im memory. Persisting is done by calling the
tree, or a part of it. You can check sync state of a node with its ``changed``
flag. If changed is ``True`` it means either that the node attributes or node
children has changed::

    >>> root.changed
    True
    
    >>> root()
    >>> root.changed
    False

Modify a LDAP node.::

    >>> person = root['cn=person1']

Modify existing attribute.::

    >>> person.attrs['sn'] = 'Mustermensch'

Add new attribute.::

    >>> person.attrs['description'] = 'Mustermensch description'
    >>> person()

Delete an attribute.::

    >>> del person.attrs['description']
    >>> person()

Delete LDAP node.::

    >>> del root['cn=person2']
    >>> root()
    >>> root.printtree()
    <ou=demo,dc=my-domain,dc=com - False>
      <cn=person1,ou=demo,dc=my-domain,dc=com:cn=person1 - False>


Searching LDAP
--------------

Add some users and groups we'll search for.::

    >>> for i in range(2, 6):
    ...     node = LDAPNode()
    ...     node.attrs['objectClass'] = ['person']
    ...     node.attrs['sn'] = 'Surname %s' % i
    ...     node.attrs['userPassword'] = 'secret%s' % i
    ...     node.attrs['description'] = 'group1'
    ...     root['cn=person%s' % i] = node
    
    >>> node = LDAPNode()
    >>> node.attrs['objectClass'] = ['groupOfNames']
    >>> node.attrs['member'] = [
    ...     root.child_dn('cn=person1'),
    ...     root.child_dn('cn=person2'),
    ... ]
    ... node.attrs['description'] = 'IT'
    >>> root['cn=group1'] = node
    
    >>> node = LDAPNode()
    >>> node.attrs['objectClass'] = ['groupOfNames']
    >>> node.attrs['member'] = [
    ...     root.child_dn('cn=person4'),
    ...     root.child_dn('cn=person5'),
    ... ]
    >>> root['cn=group2'] = node
    
    >>> root()
    >>> root.printtree()
    <ou=demo,dc=my-domain,dc=com - False>
      <cn=person1,ou=demo,dc=my-domain,dc=com:cn=person1 - False>
      <cn=person2,ou=demo,dc=my-domain,dc=com:cn=person2 - False>
      <cn=person3,ou=demo,dc=my-domain,dc=com:cn=person3 - False>
      <cn=person4,ou=demo,dc=my-domain,dc=com:cn=person4 - False>
      <cn=person5,ou=demo,dc=my-domain,dc=com:cn=person5 - False>
      <cn=group1,ou=demo,dc=my-domain,dc=com:cn=group1 - False>
      <cn=group2,ou=demo,dc=my-domain,dc=com:cn=group2 - False>

For defining search criteria LDAP filter are used, which can be combined by
bool operators '&' and '|'.::

    >>> from node.ext.ldap import LDAPFilter
    >>> filter = LDAPFilter('(objectClass=person)')
    >>> filter |= LDAPFilter('(objectClass=groupOfNames)')
    >>> root.search(queryFilter=filter)
    [u'cn=person1', 
    u'cn=person2', 
    u'cn=person3', 
    u'cn=person4', 
    u'cn=person5', 
    u'cn=group1', 
    u'cn=group2']

Define multiple criteria LDAP filter.::

    >>> from node.ext.ldap import LDAPDictFilter
    >>> filter = LDAPDictFilter({'objectClass': ['person'], 'cn': 'person1'})
    >>> root.search(queryFilter=filter)
    [u'cn=person1']

Define a relation LDAP filter. In this case we build a relation between group
'cn' and person 'description'::

    >>> from node.ext.ldap import LDAPRelationFilter
    >>> filter = LDAPRelationFilter(root['cn=group1'], 'cn:description')
    >>> root.search(queryFilter=filter)
    [u'cn=person2', 
    u'cn=person3', 
    u'cn=person4', 
    u'cn=person5']

The different LDAP filter types can be combined.::

    >>> filter &= LDAPFilter('(cn=person2)')
    >>> str(filter) 
    '(&(description=group1)(cn=person2))'

All keyword arguments accepted by ``LDAPNode.search``. If multiple keywords are
given, search criteria is '&' combined where appropriate:
    
queryFilter
    Either a LDAP filter instance or a string. If given argument is string type,
    a ``LDAPFilter`` instance is created.
    
criteria
    A dictionary containing search criteria. A ``LDAPDictFilter`` instance is
    created.

attrlist
    List of attribute names to return.
 
relation
    Either ``LDAPRelationFilter`` instance or a string defining the relation.
    If given argument is string type, a ``LDAPRelationFilter`` instance is
    created.
    
relation_node
    In combination with ``relation`` argument, when given as string, use
    ``relation_node`` instead of self for filter creation.  

exact_match
    Flag whether 1-length result is expected. Raises an error if empty result
    or more than one entry found.

or_search
    In combination with ``criteria``, this parameter is passed to the creation
    of LDAPDictFilter controlling whether to combine criteria with '&' or '|'.

You can define search defaults on the node which are always considered when
callins ``search`` on this node. If set, they are always '&' combined with
the optional passed filters.

Define the default search scope::

    >>> from node.ext.ldap import SUBTREE
    >>> root.search_scope = SUBTREE

Define default search filter, could be of type LDAPFilter, LDAPDictFilter,
LDAPRelationFilter or string.:

    >>> root.search_filter = LDAPFilter('objectClass=groupOfNames')
    >>> root.search()
    [u'cn=group1', u'cn=group2']

    >>> root.search_filter = None

Define default search criteria as dict.::
    
    >>> root.search_criteria = {'objectClass': 'person'}
    >>> root.search()
    [u'cn=person1', 
    u'cn=person2', 
    u'cn=person3', 
    u'cn=person4', 
    u'cn=person5']

Define default search relation.::

    >>> root.search_relation = \
    ...     LDAPRelationFilter(root['cn=group1'], 'cn:description')
    >>> root.search()
    [u'cn=person2', 
    u'cn=person3', 
    u'cn=person4', 
    u'cn=person5']

Again, like with the keyword arguments, multiple defined defaults are '&'
combined.::

    # empty result, ther are no groups with group 'cn' as 'description' 
    >>> root.search_criteria = {'objectClass': 'group'}
    >>> root.search()
    []


Character Encoding
------------------

LDAP (v3 at least, `RFC 2251`_) uses utf8 string encoding. ``LDAPSession`` and 
``LDAPNode`` do translation for you. Consider it a bug, if you receive anything
else than unicode from ``LDAPSession`` or ``LDAPNode``. Everything below that
``LDAPConnector`` and ``LDAPCommunicator`` give you the real ldap experience.

Unicode strings you pass to nodes or sessions are automatically encoded to uft8
for LDAP. If you feed them normal strings they are decoded as utf8 and
reencoded as utf8 to make sure they are utf8 or compatible, e.g. ascii.

If decoding as utf8 fails, the value is assumed to be in binary and left as a
string. This is not the final behavior since schema parsing is missing.

If you have an LDAP server that does not use utf8, monkey-patch
``node.ext.ldap._node.CHARACTER_ENCODING``.


Caching Support
---------------

``node.ext.ldap`` can cache LDAP searches using ``bda.cache``. You need 
to provide a cache factory utility in you application in order to make caching
work. If you don't, ``node.ext.ldap`` falls back to use ``bda.cache.NullCache``,
which does not cache anything and is just an API placeholder. 

To provide an cache based on ``Memcached`` install memcached server and
configure it. Then you need to provide the factory utility.::

    >>> # Dummy registry.
    >>> from zope.component import registry
    >>> components = registry.Components('comps')
    
    >>> from node.ext.ldap.cache import MemcachedProviderFactory
    >>> cache_factory = MemcachedProviderFactory()
    >>> components.registerUtility(cache_factory)
    
In case of multiple memcached backends running or not running on
127.0.0.1 at default port, initialization of factory looks like this.::    

    >>> # Dummy registry.
    >>> components = registry.Components('comps')
    
    >>> cache_factory = MemcachedProviderFactory(servers=['10.0.0.10:22122',
    ...                                                   '10.0.0.11:22322'])
    >>> components.registerUtility(cache_factory)


Dependencies
------------

- python-ldap
- node
- node.ext.ldap
- bda.cache
- bda.basen


Notes on python-ldap
--------------------

There are different compile issues on different platforms. If you experience
problems with ``python-ldap``, make sure it is available in the python
environment you run buildout in, so it won't be fetched and build by buildout
itself.


TODO
====

- TLS/SSL Support. in ``LDAPConnector``
  could be useful: python-ldap's class SmartLDAPObject(ReconnectLDAPObject) -
  Mainly the __init__() method does some smarter things like negotiating the
  LDAP protocol version and calling LDAPObject.start_tls_s().
  XXX: SmartLDAPObject has been removed from the most recent python-ldap,
  because of being too buggy.

- define how our retry logic should look like, re-think job of session,
  communicator and connector. (check ldap.ldapobject.ReconnectLDAPObject)
  ideas: more complex retry logic with fallback servers, eg. try immediately
  again, if fails use backup server, start to test other server after
  timespan, report status of ldap servers, preferred server, equal servers,
  load balance; Are there ldap load balancers to recommend?

- consider search_st with timeout.

- investigate ``ReconnectLDAPObject.set_cache_options``

- check/implement silent sort on only the keys ``LDAPNode.sortonkeys``

- binary attributes: 1. introduce Binary: ``node['cn=foo'].attrs['image']
  = Binary(stream)``, 2. parse ldap schema to identify binary attributes, also
  further types like BOOL

- node.ext.ldap.filter unicode/utf-8

- auto-detection of rdn attribute.

- interactive configuration showing life how many users/groups are found with
  the current config and how a selected user/group would look like


Changes
=======

0.9dev
------

- refactor form ``bda.ldap``.
  [rnix, chaoflow]


Contributors
============

- Robert Niederreiter <rnix@squarewave.at>

- Florian Friesdorf <flo@chaoflow.net>

- Jens Klein <jens@bluedynamics.com>

- Georg Bernhard <g.bernhard@akbild.ac.at>

- Johannes Raggam <johannes@bluedynamics.com>
