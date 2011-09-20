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

.. contents::
    :depth: 2


Usage
=====


LDAP Properties
---------------

To define connection properties for LDAP use ``node.ext.ldap.LDAPProps``
object::

    >>> from node.ext.ldap import LDAPProps    
    >>> props = LDAPProps(uri='ldap://localhost:12345/',
    ...                   user='cn=Manager,dc=my-domain,dc=com',
    ...                   password='secret',
    ...                   cache=False)

Test server connectivity with ``node.ext.ldap.testLDAPConnectivity``::

    >>> from node.ext.ldap import testLDAPConnectivity
    >>> testLDAPConnectivity(props=props)
    'success'


LDAP Connection
---------------

For handling LDAP connections, ``node.ext.ldap.LDAPConnector`` is used. It
expects a ``LDAPProps`` instance in the constructor. Normally there is no
need to instantiate this object directly, this happens during creation of
higher abstractions, see below::

    >>> from node.ext.ldap import LDAPConnector
    >>> connector = LDAPConnector(props=props)
    >>> connector
    <node.ext.ldap.base.LDAPConnector object at ...>

Calling ``bind`` creates and returns the LDAP connection::

    >>> connector.bind()
    <ldap.ldapobject.SimpleLDAPObject instance at ...>

Calling ``unbind`` destroys the connection::

    >>> connector.unbind()


LDAP Communication
------------------

For communicating with an LDAP server, ``node.ext.ldap.LDAPCommunicator`` is
used. It provides all the basic functions needed to search and modify the
directory.

``LDAPCommunicator`` expects a ``LDAPConnector`` instance at creation time::

    >>> from node.ext.ldap import LDAPCommunicator
    >>> communicator = LDAPCommunicator(connector)
    >>> communicator
    <node.ext.ldap.base.LDAPCommunicator object at ...>

Bind to server::

    >>> communicator.bind()

Adding directory entry::

    >>> communicator.add(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     {
    ...         'cn': 'foo',
    ...         'sn': 'Mustermann',
    ...         'userPassword': 'secret',
    ...         'objectClass': ['person'],
    ...     })

Set default search DN::

    >>> communicator.baseDN = 'ou=demo,dc=my-domain,dc=com'

Search in directory::

    >>> import node.ext.ldap
    >>> communicator.search('(objectClass=person)', node.ext.ldap.SUBTREE)
    [('cn=foo,ou=demo,dc=my-domain,dc=com', 
    {'objectClass': ['person'], 
    'userPassword': ['secret'], 
    'cn': ['foo'], 
    'sn': ['Mustermann']})]

Modify directory entry::

    >>> from ldap import MOD_REPLACE
    >>> communicator.modify('cn=foo,ou=demo,dc=my-domain,dc=com',
    ...                     [(MOD_REPLACE, 'sn', 'Musterfrau')])
    
    >>> communicator.search('(objectClass=person)',
    ...                     node.ext.ldap.SUBTREE,
    ...                     attrlist=['cn'])
    [('cn=foo,ou=demo,dc=my-domain,dc=com', 
    {'cn': ['foo']})]

Change the password of a directory entry which represents a user::

    >>> communicator.passwd(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com', 'secret', '12345')
    
    >>> communicator.search('(objectClass=person)',
    ...                     node.ext.ldap.SUBTREE,
    ...                     attrlist=['userPassword'])
    [('cn=foo,ou=demo,dc=my-domain,dc=com', 
    {'userPassword': ['{SSHA}...']})]

Delete directory entry::

    >>> communicator.delete('cn=foo,ou=demo,dc=my-domain,dc=com')
    
    >>> communicator.search('(objectClass=person)', node.ext.ldap.SUBTREE)
    []

Close connection::

    >>> communicator.unbind()


LDAP Session
------------

A more convenient way for dealing with LDAP is provided by
``node.ext.ldap.LDAPSession``. It basically provides the same functionality
as ``LDAPCommunicator``, but automatically creates the connectivity objects
and checks the connection state before performing actions.

Instantiate ``LDAPSession`` object. Expects ``LDAPProps`` instance::

    >>> from node.ext.ldap import LDAPSession
    >>> session = LDAPSession(props)

LDAP session has a convenience to check given properties::

    >>> session.checkServerProperties()
    (True, 'OK')

Set default search DN for session::

    >>> session.baseDN = 'ou=demo,dc=my-domain,dc=com'

Search in directory::

    >>> session.search()
    [(u'ou=demo,dc=my-domain,dc=com', 
    {u'objectClass': [u'top', u'organizationalUnit'], 
    u'ou': [u'demo'], 
    u'description': [u'Demo organizational unit']})]

Add directory entry::

    >>> session.add(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     {
    ...         'cn': 'foo',
    ...         'sn': 'Mustermann',
    ...         'userPassword': 'secret',
    ...         'objectClass': ['person'],
    ...     })

Change the password of a directory entry which represents a user::

    >>> session.passwd('cn=foo,ou=demo,dc=my-domain,dc=com', 'secret', '12345')

Authenticate a specific user::

    >>> session.authenticate('cn=foo,ou=demo,dc=my-domain,dc=com', '12345')
    True

Modify directory entry::
    
    >>> session.modify('cn=foo,ou=demo,dc=my-domain,dc=com',
    ...                [(MOD_REPLACE, 'sn', 'Musterfrau')])
    
    >>> session.search('(objectClass=person)',
    ...                node.ext.ldap.SUBTREE,
    ...                attrlist=['cn'])
    [(u'cn=foo,ou=demo,dc=my-domain,dc=com', {u'cn': [u'foo']})]

Delete directory entry::

    >>> session.delete('cn=foo,ou=demo,dc=my-domain,dc=com')
    >>> session.search('(objectClass=person)', node.ext.ldap.SUBTREE)
    []

Close session::

    >>> session.unbind()


LDAP Nodes
----------

One can deal with LDAP entries as node objects. Therefor
``node.ext.ldap.LDAPNode`` is used. To get a clue of the complete
node API, see `node <http://pypi.python.org/pypi/node>`_ package.

Create a LDAP node. The root Node expects the base DN and a ``LDAPProps``
instance::

    >>> from node.ext.ldap import LDAPNode
    >>> root = LDAPNode('ou=demo,dc=my-domain,dc=com', props=props)

Every LDAP node has a DN and a RDN::

    >>> root.DN
    u'ou=demo,dc=my-domain,dc=com'
    
    >>> root.rdn_attr
    u'ou'

Directory entry has no children yet::

    >>> root.keys()
    []
    
Add children to root node::

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
node key and set automatically::

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

Have a look at the tree::

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

Modify a LDAP node::

    >>> person = root['cn=person1']

Modify existing attribute::

    >>> person.attrs['sn'] = 'Mustermensch'

Add new attribute::

    >>> person.attrs['description'] = 'Mustermensch description'
    >>> person()

Delete an attribute::

    >>> del person.attrs['description']
    >>> person()

Delete LDAP node::

    >>> del root['cn=person2']
    >>> root()
    >>> root.printtree()
    <ou=demo,dc=my-domain,dc=com - False>
      <cn=person1,ou=demo,dc=my-domain,dc=com:cn=person1 - False>


Searching LDAP
--------------

Add some users and groups we'll search for::

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

For defining search criteria LDAP filters are used, which can be combined by
bool operators '&' and '|'::

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

Define multiple criteria LDAP filter::

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

Different LDAP filter types can be combined::

    >>> filter &= LDAPFilter('(cn=person2)')
    >>> str(filter) 
    '(&(description=group1)(cn=person2))'

The following keyword arguments are accepted by ``LDAPNode.search``. If multiple keywords are
used, combine search criteria with '&' where appropriate:
    
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
calling ``search`` on this node. If set, they are always '&' combined with
any (optional) passed filters.

Define the default search scope::

    >>> from node.ext.ldap import SUBTREE
    >>> root.search_scope = SUBTREE

Define default search filter, could be of type LDAPFilter, LDAPDictFilter,
LDAPRelationFilter or string::

    >>> root.search_filter = LDAPFilter('objectClass=groupOfNames')
    >>> root.search()
    [u'cn=group1', u'cn=group2']

    >>> root.search_filter = None

Define default search criteria as dict::
    
    >>> root.search_criteria = {'objectClass': 'person'}
    >>> root.search()
    [u'cn=person1', 
    u'cn=person2', 
    u'cn=person3', 
    u'cn=person4', 
    u'cn=person5']

Define default search relation::

    >>> root.search_relation = \
    ...     LDAPRelationFilter(root['cn=group1'], 'cn:description')
    >>> root.search()
    [u'cn=person2', 
    u'cn=person3', 
    u'cn=person4', 
    u'cn=person5']

Again, like with the keyword arguments, multiple defined defaults are '&'
combined::

    # empty result, there are no groups with group 'cn' as 'description' 
    >>> root.search_criteria = {'objectClass': 'group'}
    >>> root.search()
    []


User and Group management
-------------------------

LDAP is often used to manage Authentication, thus ``node.ext.ldap`` provides
an API for User and Group management. The API follows the contract of
`node.ext.ugm <http://pypi.python.org/pypi/node.ext.ugm>`_::

    >>> from node.ext.ldap import ONELEVEL
    >>> from node.ext.ldap.ugm import (
    ...     UsersConfig,
    ...     GroupsConfig,
    ...     RolesConfig,
    ...     Ugm,
    ... )

Instantiate users, groups and roles configuration. They are based on
``PrincipalsConfig`` class and expect this settings:

baseDN
    Principals container base DN.

attrmap
    Principals Attribute map as ``odict.odict``. This object must contain the
    mapping between reserved keys and the real LDAP attribute, as well as
    mappings to all accessible attributes for principal nodes if instantiated
    in strict mode, see below.

scope
    Search scope for principals.

queryFilter
    Search Query filter for principals

objectClasses
    Object classes used for creation of new principals. For some objectClasses
    default value callbacks are registered, which are used to generate default
    values for mandatory attributes if not already set on principal vessel node. 
    
defaults
    Dict like object containing default values for principal creation. A value 
    could either be static or a callable accepting the principals node and the
    new principal id as arguments. This defaults take precedence to defaults
    detected via set object classes.

strict
    Define whether all available principal attributes must be declared in attmap,
    or only reserved ones. Defaults to True.

Reserved attrmap keys for Users, Groups and roles:

id
    The attribute containing the user id (mandatory).

rdn
    The attribute representing the RDN of the node (mandatory)
    XXX: get rid of, should be detected automatically

Reserved attrmap keys for Users:

login
    Alternative login name attribute (optional)

Create config objects::

    >>> ucfg = UsersConfig(
    ...     baseDN='ou=demo,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'cn',
    ...         'rdn': 'cn',
    ...         'login': 'sn',
    ...     },
    ...     scope=ONELEVEL,
    ...     queryFilter='(objectClass=person)',
    ...     objectClasses=['person'],
    ...     defaults={},
    ...     strict=False,
    ... )
    
    >>> gcfg = GroupsConfig(
    ...     baseDN='ou=demo,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'cn',
    ...         'rdn': 'cn',
    ...     },
    ...     scope=ONELEVEL,
    ...     queryFilter='(objectClass=groupOfNames)',
    ...     objectClasses=['groupOfNames'],
    ...     defaults={},
    ...     strict=False,
    ... )

Roles are represented in LDAP like groups. Note, if groups and roles are mixed
up in the same container, make sure that query filter fits. For our demo,
different group object classes are used. Anyway, in real world it might be
worth considering a seperate container for roles::

    >>> rcfg = GroupsConfig(
    ...     baseDN='ou=demo,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'cn',
    ...         'rdn': 'cn',
    ...     },
    ...     scope=ONELEVEL,
    ...     queryFilter='(objectClass=groupOfUniqueNames)',
    ...     objectClasses=['groupOfUniqueNames'],
    ...     defaults={},
    ...     strict=False,
    ... )

Instantiate ``Ugm`` object::

    >>> ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)
    >>> ugm
    <Ugm object 'None' at ...>

The Ugm object has 2 children, the users container and the groups container.
The are accessible via node API, but also on ``users`` respective ``groups``
attribute::

    >>> ugm.keys()
    ['users', 'groups']
    
    >>> ugm.users
    <Users object 'users' at ...>
    
    >>> ugm.groups
    <Groups object 'groups' at ...>

Fetch user::

    >>> user = ugm.users['person1']
    >>> user
    <User object 'person1' at ...>

User attributes. Reserved keys are available on user attributes::

    >>> user.attrs['id']
    u'person1'
    
    >>> user.attrs['login']
    u'Mustermensch'

'login' maps to 'sn'::

    >>> user.attrs['sn']
    u'Mustermensch'

    >>> user.attrs['login'] = u'Mustermensch1'
    >>> user.attrs['sn']
    u'Mustermensch1'

    >>> user.attrs['description'] = 'Some description'
    >>> user()

Check user credentials::

    >>> user.authenticate('secret')
    True

Change user password::

    >>> user.passwd('secret', 'newsecret')
    >>> user.authenticate('newsecret')
    True

Groups user is member of::

    >>> user.groups
    [<Group object 'group1' at ...>]

Add new User::

    >>> user = ugm.users.create('person99', sn='Person 99')
    >>> user()
    
    >>> ugm.users.keys()
    [u'person1', 
    u'person2', 
    u'person3', 
    u'person4', 
    u'person5', 
    u'person99']

Delete User::

    >>> del ugm.users['person99']
    >>> ugm.users()
    >>> ugm.users.keys()
    [u'person1', 
    u'person2', 
    u'person3', 
    u'person4', 
    u'person5']

Fetch Group::

    >>> group = ugm.groups['group1']

Group members::

    >>> group.member_ids
    [u'person1', u'person2']
    
    >>> group.users
    [<User object 'person1' at ...>, <User object 'person2' at ...>]  

Add group member::

    >>> group.add('person3')
    >>> group.member_ids
    [u'person1', u'person2', u'person3']
    
Delete group member::

    >>> del group['person3']
    >>> group.member_ids
    [u'person1', u'person2']

Group attribute manipulation works the same way as on user objects.

Manage roles for users and groups. Roles can be queried, added and removed via
ugm or principal object. Fetch a user::

    >>> user = ugm.users['person1']

Add role for user via ugm::

    >>> ugm.add_role('viewer', user)

Add role for user directly::

    >>> user.add_role('editor')

Query roles for user via ugm::

    >>> ugm.roles(user)
    [u'viewer', u'editor']

Query roles directly::

    >>> user.roles
    [u'viewer', u'editor']

Call UGM to persist roles::

    >>> ugm()

Delete role via ugm::

    >>> ugm.remove_role('viewer', user)
    >>> user.roles
    [u'editor']

Delete role directly::

    >>> user.remove_role('editor')
    >>> user.roles
    []

Call UGM to persist roles::

    >>> ugm()

Same with group. Fetch a group::

    >>> group = ugm.groups['group1']

Add roles::
    
    >>> ugm.add_role('viewer', group)
    >>> group.add_role('editor')
    
    >>> ugm.roles(group)
    [u'viewer', u'editor']
    
    >>> group.roles
    [u'viewer', u'editor']
    
    >>> ugm()

Remove roles::

    >>> ugm.remove_role('viewer', group)
    >>> group.remove_role('editor')
    >>> group.roles
    []
    
    >>> ugm()


Character Encoding
------------------

LDAP (v3 at least, `RFC 2251`_) uses utf8 string encoding. ``LDAPSession`` and 
``LDAPNode`` do the encoding for you. Consider it a bug, if you receive 
anything else than unicode from ``LDAPSession`` or ``LDAPNode``. The 
``LDAPConnector`` and ``LDAPCommunicator`` are encoding-neutral, they do no 
decoding or encoding.

Unicode strings you pass to nodes or sessions are automatically encoded as uft8
for LDAP. If you feed them ordinary strings they are decoded as utf8 and
reencoded as utf8 to make sure they are utf8 or compatible, e.g. ascii.

If decoding as utf8 fails, the value is assumed to be binary and left 
unaltered. This is not the final behavior since schema parsing is missing.

If you have an LDAP server that does not use utf8, monkey-patch
``node.ext.ldap._node.CHARACTER_ENCODING``.


Caching Support
---------------

``node.ext.ldap`` can cache LDAP searches using ``bda.cache``. You need 
to provide a cache factory utility in you application in order to make caching
work. If you don't, ``node.ext.ldap`` falls back to use ``bda.cache.NullCache``,
which does not cache anything and is just an API placeholder. 

To provide a cache based on ``Memcached`` install memcached server and
configure it. Then you need to provide the factory utility::

    >>> # Dummy registry.
    >>> from zope.component import registry
    >>> components = registry.Components('comps')
    
    >>> from node.ext.ldap.cache import MemcachedProviderFactory
    >>> cache_factory = MemcachedProviderFactory()
    >>> components.registerUtility(cache_factory)
    
In case of multiple memcached backends on various IPs and ports initialization
of the factory looks like this::    

    >>> # Dummy registry.
    >>> components = registry.Components('comps')
    
    >>> cache_factory = MemcachedProviderFactory(servers=['10.0.0.10:22122',
    ...                                                   '10.0.0.11:22322'])
    >>> components.registerUtility(cache_factory)


Dependencies
------------

- python-ldap
- smbpasswd
- argparse
- plumber
- node
- node.ext.ugm
- bda.cache


Notes on python-ldap
--------------------

There are different compile issues on different platforms. If you experience
problems with ``python-ldap``, make sure it is available in the python
environment you run buildout in, so it won't be fetched and built by buildout
itself.


Test Coverage
-------------

Summary of the test coverage report::

  lines   cov%   module
      6   100%   node.ext.ldap.__init__
    409   100%   node.ext.ldap._node
    115   100%   node.ext.ldap.base
     13   100%   node.ext.ldap.cache
    101   100%   node.ext.ldap.filter
     46   100%   node.ext.ldap.interfaces
     28   100%   node.ext.ldap.properties
      6   100%   node.ext.ldap.scope
     60   100%   node.ext.ldap.session
    462   100%   node.ext.ldap.testing.__init__
     27   100%   node.ext.ldap.tests
      1   100%   node.ext.ldap.ugm.__init__
    576   100%   node.ext.ldap.ugm._api
     21   100%   node.ext.ldap.ugm.defaults
     17   100%   node.ext.ldap.ugm.posix
     26   100%   node.ext.ldap.ugm.samba
     21   100%   node.ext.ldap.ugm.shadow


TODO
====

- TLS/SSL Support. in ``LDAPConnector``
  could be useful: python-ldap's class SmartLDAPObject(ReconnectLDAPObject) -
  Mainly the __init__() method does some smarter things like negotiating the
  LDAP protocol version and calling LDAPObject.start_tls_s().
  XXX: SmartLDAPObject has been removed from the most recent python-ldap,
  because of being too buggy.

- define what our retry logic should look like, re-think function of session,
  communicator and connector. (check ldap.ldapobject.ReconnectLDAPObject)
  ideas: more complex retry logic with fallback servers, eg. try immediately
  again, if that fails use backup server, then start to probe other server 
  after a timespan, report status of ldap servers, preferred server, 
  equal servers, load balancing; Are there ldap load balancers to recommend?

- consider search_st with timeout.

- investigate ``ReconnectLDAPObject.set_cache_options``

- check/implement silent sort on only the keys ``LDAPNode.sortonkeys``

- binary attributes: 1. introduce Binary: ``node['cn=foo'].attrs['image']
  = Binary(stream)``, 2. parse ldap schema to identify binary attributes, also
  further types like BOOL

- node.ext.ldap.filter unicode/utf-8

- auto-detection of rdn attribute.

- interactive configuration showing live how many users/groups are found with
  the current config and what a selected user/group would look like

- Scope SUBTREE for Principals containers is not tested properly yet.
  Especially ``__getitem__`` needs a little love.

- Configuration validation for UGM. Add some checks in ``Ugm.__init__`` which
  tries to block stupid configuration.


Changes
=======

0.9
---

- refactor form ``bda.ldap``.
  [rnix, chaoflow]


Contributors
============

- Robert Niederreiter <rnix [at] squarewave [dot] at>

- Florian Friesdorf <flo [at] chaoflow [dot] net>

- Jens Klein <jens [at] bluedynamics [dot] com>

- Georg Bernhard <g.bernhard [at] akbild [dot] ac [dot] at>

- Johannes Raggam <johannes [at] bluedynamics [dot] com>
