.. image:: https://travis-ci.org/bluedynamics/node.ext.ldap.svg?branch=master
    :target: https://travis-ci.org/bluedynamics/node.ext.ldap

.. image:: https://coveralls.io/repos/bluedynamics/node.ext.ldap/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/bluedynamics/node.ext.ldap?branch=master

.. image:: https://img.shields.io/pypi/v/node.ext.ldap
        :alt: Latest stable release on PyPI
        :target: https://pypi.org/project/node.ext.ldap/


Overview
========

``node.ext.ldap`` is a LDAP convenience library for LDAP communication based on
`python-ldap <http://pypi.python.org/pypi/python-ldap>`_ (version 2.4 or later)
and `node <http://pypi.python.org/pypi/node>`_.

The package contains base configuration and communication objects, a LDAP node
object and a LDAP node based user and group management implementation utilizing
`node.ext.ugm <http://pypi.python.org/pypi/node.ext.ugm>`_.

.. _`RFC 2251`: http://www.ietf.org/rfc/rfc2251.txt

This package is the successor of
`bda.ldap <http://pypi.python.org/pypi/bda.ldap>`_.

.. contents::
    :depth: 2


API changes compared to 0.9.x
=============================

- ``LDAPNode`` instances cannot have direct children of subtree any longer.
  This was a design flaw because of possible duplicate RDN's.

- ``LDAPNode.search`` returns DN's instead of RDN's by default.

- Secondary keys and alternative key attribute features have been removed
  entirely from ``LDAPNode``.

- ``LDAPProps.check_duplicates`` setting has been removed.


Usage
=====


LDAP Properties
---------------

To define connection properties for LDAP use ``node.ext.ldap.LDAPProps``
object:

.. code-block:: pycon

    >>> from node.ext.ldap import LDAPProps

    >>> props = LDAPProps(
    ...     uri='ldap://localhost:12345/',
    ...     user='cn=Manager,dc=my-domain,dc=com',
    ...     password='secret',
    ...     cache=False
    ... )

Test server connectivity with ``node.ext.ldap.testLDAPConnectivity``:

.. code-block:: pycon

    >>> from node.ext.ldap import testLDAPConnectivity

    >>> assert testLDAPConnectivity(props=props) == 'success'


LDAP Connection
---------------

For handling LDAP connections, ``node.ext.ldap.LDAPConnector`` is used. It
expects a ``LDAPProps`` instance in the constructor. Normally there is no
need to instantiate this object directly, this happens during creation of
higher abstractions, see below:

.. code-block:: pycon

    >>> from node.ext.ldap import LDAPConnector
    >>> import ldap

    >>> connector = LDAPConnector(props=props)

Calling ``bind`` creates and returns the LDAP connection:

.. code-block:: pycon

    >>> conn = connector.bind()
    >>> assert isinstance(conn, ldap.ldapobject.ReconnectLDAPObject)

Calling ``unbind`` destroys the connection:

.. code-block:: pycon

    >>> connector.unbind()


LDAP Communication
------------------

For communicating with an LDAP server, ``node.ext.ldap.LDAPCommunicator`` is
used. It provides all the basic functions needed to search and modify the
directory.

``LDAPCommunicator`` expects a ``LDAPConnector`` instance at creation time:

.. code-block:: pycon

    >>> from node.ext.ldap import LDAPCommunicator

    >>> communicator = LDAPCommunicator(connector)

Bind to server:

.. code-block:: pycon

    >>> communicator.bind()

Adding directory entry:

.. code-block:: pycon

    >>> communicator.add(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     {
    ...         'cn': 'foo',
    ...         'sn': 'Mustermann',
    ...         'userPassword': 'secret',
    ...         'objectClass': ['person'],
    ...     }
    ... )

Set default search DN:

.. code-block:: pycon

    >>> communicator.baseDN = 'ou=demo,dc=my-domain,dc=com'

Search in directory:

.. code-block:: pycon

    >>> import node.ext.ldap

    >>> res = communicator.search(
    ...     '(objectClass=person)',
    ...     node.ext.ldap.SUBTREE
    ... )

    >>> assert res == [(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     {
    ...         'objectClass': ['person'],
    ...         'userPassword': ['secret'],
    ...         'cn': ['foo'],
    ...         'sn': ['Mustermann']
    ...     }
    ... )]

Modify directory entry:

.. code-block:: pycon

    >>> from ldap import MOD_REPLACE

    >>> communicator.modify(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     [(MOD_REPLACE, 'sn', 'Musterfrau')]
    ... )

    >>> res = communicator.search(
    ...     '(objectClass=person)',
    ...     node.ext.ldap.SUBTREE,
    ...     attrlist=['cn']
    ... )

    >>> assert res == [('cn=foo,ou=demo,dc=my-domain,dc=com', {'cn': ['foo']})]

Change the password of a directory entry which represents a user:

.. code-block:: pycon

    >>> communicator.passwd(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     'secret',
    ...     '12345'
    ... )

    >>> res = communicator.search(
    ...     '(objectClass=person)',
    ...     node.ext.ldap.SUBTREE,
    ...     attrlist=['userPassword']
    ... )

    >>> assert res == [(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     {'userPassword': ['{SSHA}...']}
    ... )]

Delete directory entry:

.. code-block:: pycon

    >>> communicator.delete('cn=foo,ou=demo,dc=my-domain,dc=com')

    >>> res = communicator.search(
    ...     '(objectClass=person)',
    ...     node.ext.ldap.SUBTREE
    ... )

    >>> assert res == []

Close connection:

.. code-block:: pycon

    >>> communicator.unbind()


LDAP Session
------------

A more convenient way for dealing with LDAP is provided by
``node.ext.ldap.LDAPSession``. It basically provides the same functionality
as ``LDAPCommunicator``, but automatically creates the connectivity objects
and checks the connection state before performing actions.

Instantiate ``LDAPSession`` object. Expects ``LDAPProps`` instance:

.. code-block:: pycon

    >>> from node.ext.ldap import LDAPSession

    >>> session = LDAPSession(props)

LDAP session has a convenience to check given properties:

.. code-block:: pycon

    >>> res = session.checkServerProperties()

    >>> assert res == (True, 'OK')

Set default search DN for session:

.. code-block:: pycon

    >>> session.baseDN = 'ou=demo,dc=my-domain,dc=com'

Search in directory:

.. code-block:: pycon

    >>> res = session.search()

    >>> assert res == [
    ...     ('ou=demo,dc=my-domain,dc=com',
    ...     {
    ...         'objectClass': ['top', 'organizationalUnit'],
    ...         'ou': ['demo'],
    ...         'description': ['Demo organizational unit']
    ...     }
    ... )]

Add directory entry:

.. code-block:: pycon

    >>> session.add(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     {
    ...         'cn': 'foo',
    ...         'sn': 'Mustermann',
    ...         'userPassword': 'secret',
    ...         'objectClass': ['person'],
    ...     }
    ... )

Change the password of a directory entry which represents a user:

.. code-block:: pycon

    >>> session.passwd('cn=foo,ou=demo,dc=my-domain,dc=com', 'secret', '12345')

Authenticate a specific user:

.. code-block:: pycon

    >>> res = session.authenticate('cn=foo,ou=demo,dc=my-domain,dc=com', '12345')

    >>> assert res is True

Modify directory entry:

.. code-block:: pycon

    >>> session.modify(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     [(MOD_REPLACE, 'sn', 'Musterfrau')]
    ... )

    >>> res = session.search(
    ...     '(objectClass=person)',
    ...     node.ext.ldap.SUBTREE,
    ...     attrlist=['cn']
    ... )

    >>> assert res == [(
    ...     'cn=foo,ou=demo,dc=my-domain,dc=com',
    ...     {'cn': ['foo']}
    ... )]

Delete directory entry:

.. code-block:: pycon

    >>> session.delete('cn=foo,ou=demo,dc=my-domain,dc=com')

    >>> res = session.search('(objectClass=person)', node.ext.ldap.SUBTREE)

    >>> assert res == []

Close session:

.. code-block:: pycon

    >>> session.unbind()


LDAP Nodes
----------

One can deal with LDAP entries as node objects. Therefor
``node.ext.ldap.LDAPNode`` is used. To get a clue of the complete
node API, see `node <http://pypi.python.org/pypi/node>`_ package.

Create a LDAP node. The root Node expects the base DN and a ``LDAPProps``
instance:

.. code-block:: pycon

    >>> from node.ext.ldap import LDAPNode

    >>> root = LDAPNode('ou=demo,dc=my-domain,dc=com', props=props)

Every LDAP node has a DN and a RDN:

.. code-block:: pycon

    >>> root.DN
    u'ou=demo,dc=my-domain,dc=com'

    >>> root.rdn_attr
    u'ou'

Check whether created node exists in the database:

.. code-block:: pycon

    >>> root.exists
    True

Directory entry has no children yet:

.. code-block:: pycon

    >>> root.keys()
    []

Add children to root node:

.. code-block:: pycon

    >>> person = LDAPNode()
    >>> person.attrs['objectClass'] = ['person', 'inetOrgPerson']
    >>> person.attrs['sn'] = 'Mustermann'
    >>> person.attrs['userPassword'] = 'secret'
    >>> root['cn=person1'] = person

    >>> person = LDAPNode()
    >>> person.attrs['objectClass'] = ['person', 'inetOrgPerson']
    >>> person.attrs['sn'] = 'Musterfrau'
    >>> person.attrs['userPassword'] = 'secret'
    >>> root['cn=person2'] = person

If the RDN attribute was not set during node creation, it is computed from
node key and set automatically:

.. code-block:: pycon

    >>> person.attrs['cn']
    u'person2'

Fetch children DN by key from LDAP node:

.. code-block:: pycon

    >>> root.child_dn('cn=person1')
    u'cn=person1,ou=demo,dc=my-domain,dc=com'

Have a look at the tree:

.. code-block:: pycon

    >>> root.printtree()
    <ou=demo,dc=my-domain,dc=com - True>
      <cn=person2,ou=demo,dc=my-domain,dc=com:cn=person2 - True>
      <cn=person1,ou=demo,dc=my-domain,dc=com:cn=person1 - True>

The entries have not been written to the directory yet. When modifying a LDAP
node tree, everything happens im memory. Persisting is done by calling the
tree, or a part of it. You can check sync state of a node with its ``changed``
flag. If changed is ``True`` it means either that the node attributes or node
children has changed:

.. code-block:: pycon

    >>> root.changed
    True

    >>> root()
    >>> root.changed
    False

Modify a LDAP node:

.. code-block:: pycon

    >>> person = root['cn=person1']

Modify existing attribute:

.. code-block:: pycon

    >>> person.attrs['sn'] = 'Mustermensch'

Add new attribute:

.. code-block:: pycon

    >>> person.attrs['description'] = 'Mustermensch description'
    >>> person()

Delete an attribute:

.. code-block:: pycon

    >>> del person.attrs['description']
    >>> person()

Delete LDAP node:

.. code-block:: pycon

    >>> del root['cn=person2']
    >>> root()
    >>> root.printtree()
    <ou=demo,dc=my-domain,dc=com - False>
      <cn=person1,ou=demo,dc=my-domain,dc=com:cn=person1 - False>


Searching LDAP
--------------

Add some users and groups we'll search for:

.. code-block:: pycon

    >>> for i in range(2, 6):
    ...     node = LDAPNode()
    ...     node.attrs['objectClass'] = ['person', 'inetOrgPerson']
    ...     node.attrs['sn'] = 'Surname %s' % i
    ...     node.attrs['userPassword'] = 'secret%s' % i
    ...     node.attrs['description'] = 'description%s' % i
    ...     node.attrs['businessCategory'] = 'group1'
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
bool operators '&' and '|':

.. code-block:: pycon

    >>> from node.ext.ldap import LDAPFilter

    >>> filter = LDAPFilter('(objectClass=person)')
    >>> filter |= LDAPFilter('(objectClass=groupOfNames)')

    >>> res = sorted(root.search(queryFilter=filter))

    >>> assert res == [
    ...     u'cn=group1,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=group2,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person1,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person2,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person3,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person4,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person5,ou=demo,dc=my-domain,dc=com'
    ... ]

Define multiple criteria LDAP filter:

.. code-block:: pycon

    >>> from node.ext.ldap import LDAPDictFilter

    >>> filter = LDAPDictFilter({
    ...     'objectClass': ['person'],
    ...     'cn': 'person1'
    ... })

    >>> res = root.search(queryFilter=filter)

    >>> assert res == [u'cn=person1,ou=demo,dc=my-domain,dc=com']

Define a relation LDAP filter. In this case we build a relation between group
'cn' and person 'businessCategory':

.. code-block:: pycon

    >>> from node.ext.ldap import LDAPRelationFilter

    >>> filter = LDAPRelationFilter(root['cn=group1'], 'cn:businessCategory')

    >>> res = root.search(queryFilter=filter)

    >>> assert res == [
    ...     u'cn=person2,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person3,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person4,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person5,ou=demo,dc=my-domain,dc=com'
    ... ]

Different LDAP filter types can be combined:

.. code-block:: pycon

    >>> filter &= LDAPFilter('(cn=person2)')
    >>> str(filter)
    '(&(businessCategory=group1)(cn=person2))'

The following keyword arguments are accepted by ``LDAPNode.search``. If
multiple keywords are used, combine search criteria with '&' where appropriate.

If ``attrlist`` is given, the result items consists of 2-tuples with a dict
containing requested attributes at position 1:

**queryFilter**
    Either a LDAP filter instance or a string. If given argument is string type,
    a ``LDAPFilter`` instance is created.

**criteria**
    A dictionary containing search criteria. A ``LDAPDictFilter`` instance is
    created.

**attrlist**
    List of attribute names to return. Special attributes ``rdn`` and ``dn``
    are allowed.

**relation**
    Either ``LDAPRelationFilter`` instance or a string defining the relation.
    If given argument is string type, a ``LDAPRelationFilter`` instance is
    created.

**relation_node**
    In combination with ``relation`` argument, when given as string, use
    ``relation_node`` instead of self for filter creation.

**exact_match**
    Flag whether 1-length result is expected. Raises an error if empty result
    or more than one entry found.

**or_search**
    In combination with ``criteria``, this parameter is passed to the creation
    of LDAPDictFilter. This flag controls whether to combine criteria **keys**
    and **values** with '&' or '|'.

**or_keys**
    In combination with ``criteria``, this parameter is passed to the creation
    of LDAPDictFilter. This flag controls whether criteria **keys** are
    combined with '|' instead of '&'.

**or_values**
    In combination with ``criteria``, this parameter is passed to the creation
    of LDAPDictFilter. This flag controls whether criteria **values** are
    combined with '|' instead of '&'.

**page_size**
    Used in conjunction with ``cookie`` for querying paged results.

**cookie**
    Used in conjunction with ``page_size`` for querying paged results.

**get_nodes**
    If ``True`` result contains ``LDAPNode`` instances instead of DN's

You can define search defaults on the node which are always considered when
calling ``search`` on this node. If set, they are always '&' combined with
any (optional) passed filters.

Define the default search scope:

.. code-block:: pycon

    >>> from node.ext.ldap import SUBTREE

    >>> root.search_scope = SUBTREE

Define default search filter, could be of type LDAPFilter, LDAPDictFilter,
LDAPRelationFilter or string:

.. code-block:: pycon

    >>> root.search_filter = LDAPFilter('objectClass=groupOfNames')

    >>> res = root.search()

    >>> assert res == [
    ...     u'cn=group1,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=group2,ou=demo,dc=my-domain,dc=com'
    ... ]

    >>> root.search_filter = None

Define default search criteria as dict:

.. code-block:: pycon

    >>> root.search_criteria = {'objectClass': 'person'}

    >>> res = root.search()

    >>> assert res == [
    ...     u'cn=person1,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person2,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person3,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person4,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person5,ou=demo,dc=my-domain,dc=com'
    ... ]

Define default search relation:

.. code-block:: pycon

    >>> root.search_relation = LDAPRelationFilter(
    ...     root['cn=group1'],
    ...     'cn:businessCategory'
    ... )

    >>> res = root.search()

    >>> assert res == [
    ...     u'cn=person2,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person3,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person4,ou=demo,dc=my-domain,dc=com',
    ...     u'cn=person5,ou=demo,dc=my-domain,dc=com'
    ... ]

Again, like with the keyword arguments, multiple defined defaults are '&'
combined:

.. code-block:: pycon

    # empty result, there are no groups with group 'cn' as 'description'
    >>> root.search_criteria = {'objectClass': 'group'}

    >>> res = root.search()

    >>> assert res == []


JSON Serialization
------------------

Serialize and deserialize LDAP nodes:

.. code-block:: pycon

    >>> root = LDAPNode('ou=demo,dc=my-domain,dc=com', props=props)

Serialize children:

.. code-block:: pycon

    >>> from node.serializer import serialize

    >>> json_dump = serialize(root.values())

Clear and persist root:

.. code-block:: pycon

    >>> root.clear()

    >>> root()

Deserialize JSON dump:

.. code-block:: pycon

    >>> from node.serializer import deserialize

    >>> deserialize(json_dump, root=root)
    [<cn=person1,ou=demo,dc=my-domain,dc=com:cn=person1 - True>,
    <cn=person2,ou=demo,dc=my-domain,dc=com:cn=person2 - True>,
    <cn=person3,ou=demo,dc=my-domain,dc=com:cn=person3 - True>,
    <cn=person4,ou=demo,dc=my-domain,dc=com:cn=person4 - True>,
    <cn=person5,ou=demo,dc=my-domain,dc=com:cn=person5 - True>,
    <cn=group1,ou=demo,dc=my-domain,dc=com:cn=group1 - True>,
    <cn=group2,ou=demo,dc=my-domain,dc=com:cn=group2 - True>]

Since root has been given, created nodes were added:

.. code-block:: pycon

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

Non simple vs simple mode. Create container with children:

.. code-block:: pycon

    >>> container = LDAPNode()
    >>> container.attrs['objectClass'] = ['organizationalUnit']
    >>> root['ou=container'] = container

    >>> person = LDAPNode()
    >>> person.attrs['objectClass'] = ['person', 'inetOrgPerson']
    >>> person.attrs['sn'] = 'Mustermann'
    >>> person.attrs['userPassword'] = 'secret'
    >>> container['cn=person1'] = person

    >>> root()

Serialize in default mode contains type specific information. Thus JSON dump
can be deserialized later:

.. code-block:: pycon

    >>> serialized = serialize(container)

    >>> assert serialized == (
    ...     '{'
    ...         '"__node__": {'
    ...             '"attrs": {'
    ...                 '"objectClass": ["organizationalUnit"], '
    ...                 '"ou": "container"'
    ...             '}, '
    ...             '"children": [{'
    ...                 '"__node__": {'
    ...                     '"attrs": {'
    ...                         '"objectClass": ["person", "inetOrgPerson"], '
    ...                         '"userPassword": "secret", '
    ...                         '"sn": "Mustermann", '
    ...                         '"cn": "person1"'
    ...                     '},'
    ...                     '"class": "node.ext.ldap._node.LDAPNode", '
    ...                     '"name": "cn=person1"'
    ...                 '}'
    ...             '}], '
    ...             '"class": "node.ext.ldap._node.LDAPNode", '
    ...             '"name": "ou=container"'
    ...         '}'
    ...     '}'
    ... )

Serialize in simple mode is better readable, but not deserialzable any more:

.. code-block:: pycon

    >>> serialized = serialize(container, simple_mode=True)

    >>> assert serialized == (
    ...     '{'
    ...         '"attrs": {'
    ...             '"objectClass": ["organizationalUnit"], '
    ...             '"ou": "container"'
    ...         '}, '
    ...         '"name": "ou=container", '
    ...         '"children": [{'
    ...             '"name": "cn=person1", '
    ...             '"attrs": {'
    ...                 '"objectClass": ["person", "inetOrgPerson"], '
    ...                 '"userPassword": "secret", '
    ...                 '"sn": "Mustermann", '
    ...                 '"cn": "person1"'
    ...             '}'
    ...         '}]'
    ...     '}'
    ... )


User and Group management
-------------------------

LDAP is often used to manage Authentication, thus ``node.ext.ldap`` provides
an API for User and Group management. The API follows the contract of
`node.ext.ugm <http://pypi.python.org/pypi/node.ext.ugm>`_:

.. code-block:: pycon

    >>> from node.ext.ldap import ONELEVEL
    >>> from node.ext.ldap.ugm import UsersConfig
    >>> from node.ext.ldap.ugm import GroupsConfig
    >>> from node.ext.ldap.ugm import RolesConfig
    >>> from node.ext.ldap.ugm import Ugm

Instantiate users, groups and roles configuration. They are based on
``PrincipalsConfig`` class and expect this settings:

**baseDN**
    Principals container base DN.

**attrmap**
    Principals Attribute map as ``odict.odict``. This object must contain the
    mapping between reserved keys and the real LDAP attribute, as well as
    mappings to all accessible attributes for principal nodes if instantiated
    in strict mode, see below.

**scope**
    Search scope for principals.

**queryFilter**
    Search Query filter for principals

**objectClasses**
    Object classes used for creation of new principals. For some objectClasses
    default value callbacks are registered, which are used to generate default
    values for mandatory attributes if not already set on principal vessel node.

**defaults**
    Dict like object containing default values for principal creation. A value
    could either be static or a callable accepting the principals node and the
    new principal id as arguments. This defaults take precedence to defaults
    detected via set object classes.

**strict**
    Define whether all available principal attributes must be declared in attmap,
    or only reserved ones. Defaults to True.

**memberOfSupport**
    Flag whether to use 'memberOf' attribute (AD) or memberOf overlay
    (openldap) for Group membership resolution where appropriate.

Reserved attrmap keys for Users, Groups and roles:

**id**
    The attribute containing the user id (mandatory).

**rdn**
    The attribute representing the RDN of the node (mandatory)
    XXX: get rid of, should be detected automatically

Reserved attrmap keys for Users:

**login**
    Alternative login name attribute (optional)

Create config objects:

.. code-block:: pycon

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
    ...     memberOfSupport=False,
    ... )

Roles are represented in LDAP like groups. Note, if groups and roles are mixed
up in the same container, make sure that query filter fits. For our demo,
different group object classes are used. Anyway, in real world it might be
worth considering a seperate container for roles:

.. code-block:: pycon

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

Instantiate ``Ugm`` object:

.. code-block:: pycon

    >>> ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)

The Ugm object has 2 children, the users container and the groups container.
The are accessible via node API, but also on ``users`` respective ``groups``
attribute:

.. code-block:: pycon

    >>> ugm.keys()
    ['users', 'groups']

    >>> ugm.users
    <Users object 'users' at ...>

    >>> ugm.groups
    <Groups object 'groups' at ...>

Fetch user:

.. code-block:: pycon

    >>> user = ugm.users['person1']
    >>> user
    <User object 'person1' at ...>

User attributes. Reserved keys are available on user attributes:

.. code-block:: pycon

    >>> user.attrs['id']
    u'person1'

    >>> user.attrs['login']
    u'Mustermensch'

'login' maps to 'sn':

.. code-block:: pycon

    >>> user.attrs['sn']
    u'Mustermensch'

    >>> user.attrs['login'] = u'Mustermensch1'
    >>> user.attrs['sn']
    u'Mustermensch1'

    >>> user.attrs['description'] = 'Some description'
    >>> user()

Check user credentials:

.. code-block:: pycon

    >>> user.authenticate('secret')
    True

Change user password:

.. code-block:: pycon

    >>> user.passwd('secret', 'newsecret')
    >>> user.authenticate('newsecret')
    True

Groups user is member of:

.. code-block:: pycon

    >>> user.groups
    [<Group object 'group1' at ...>]

Add new User:

.. code-block:: pycon

    >>> user = ugm.users.create('person99', sn='Person 99')
    >>> user()

    >>> res = ugm.users.keys()

    >>> assert res == [
    ...     u'person1',
    ...     u'person2',
    ...     u'person3',
    ...     u'person4',
    ...     u'person5',
    ...     u'person99'
    ... ]

Delete User:

.. code-block:: pycon

    >>> del ugm.users['person99']
    >>> ugm.users()

    >>> res = ugm.users.keys()

    >>> assert res == [
    ...     u'person1',
    ...     u'person2',
    ...     u'person3',
    ...     u'person4',
    ...     u'person5'
    ... ]

Fetch Group:

.. code-block:: pycon

    >>> group = ugm.groups['group1']

Group members:

.. code-block:: pycon

    >>> res = group.member_ids

    >>> assert res == [u'person1', u'person2']

    >>> group.users
    [<User object 'person1' at ...>, <User object 'person2' at ...>]

Add group member:

.. code-block:: pycon

    >>> group.add('person3')

    >>> member_ids = group.member_ids

    >>> assert member_ids == [u'person1', u'person2', u'person3']

Delete group member:

.. code-block:: pycon

    >>> del group['person3']

    >>> member_ids = group.member_ids

    >>> assert member_ids == [u'person1', u'person2']

Group attribute manipulation works the same way as on user objects.

Manage roles for users and groups. Roles can be queried, added and removed via
ugm or principal object. Fetch a user:

.. code-block:: pycon

    >>> user = ugm.users['person1']

Add role for user via ugm:

.. code-block:: pycon

    >>> ugm.add_role('viewer', user)

Add role for user directly:

.. code-block:: pycon

    >>> user.add_role('editor')

Query roles for user via ugm:

.. code-block:: pycon

    >>> roles = sorted(ugm.roles(user))

    >>> assert roles == ['editor', 'viewer']

Query roles directly:

.. code-block:: pycon

    >>> roles = sorted(user.roles)

    >>> assert roles == ['editor', 'viewer']

Call UGM to persist roles:

.. code-block:: pycon

    >>> ugm()

Delete role via ugm:

.. code-block:: pycon

    >>> ugm.remove_role('viewer', user)

    >>> roles = user.roles

    >>> assert roles == ['editor']

Delete role directly:

.. code-block:: pycon

    >>> user.remove_role('editor')

    >>> roles = user.roles

    >>> assert roles == []

Call UGM to persist roles:

.. code-block:: pycon

    >>> ugm()

Same with group. Fetch a group:

.. code-block:: pycon

    >>> group = ugm.groups['group1']

Add roles:

.. code-block:: pycon

    >>> ugm.add_role('viewer', group)

    >>> group.add_role('editor')

    >>> roles = sorted(ugm.roles(group))

    >>> assert roles == ['editor', 'viewer']

    >>> roles = sorted(group.roles)

    >>> assert roles == ['editor', 'viewer']

    >>> ugm()

Remove roles:

.. code-block:: pycon

    >>> ugm.remove_role('viewer', group)

    >>> group.remove_role('editor')

    >>> roles = group.roles

    >>> assert roles == []

    >>> ugm()


Character Encoding
------------------

LDAP (v3 at least, `RFC 2251`_) uses ``utf-8`` string encoding only.
``LDAPNode`` does the encoding for you. Consider it a bug, if you receive
anything else than unicode from ``LDAPNode``, except attributes configured as
binary. The ``LDAPSession``, ``LDAPConnector`` and ``LDAPCommunicator`` are
encoding-neutral, they do no decoding or encoding.

Unicode strings you pass to nodes or sessions are automatically encoded as uft8
for LDAP, except if configured binary. If you feed them ordinary strings they are
decoded as utf8 and reencoded as utf8 to make sure they are utf8 or compatible,
e.g. ascii.

If you have an LDAP server that does not use utf8, monkey-patch
``node.ext.ldap._node.CHARACTER_ENCODING``.


Caching Support
---------------

``node.ext.ldap`` can cache LDAP searches using ``bda.cache``. You need
to provide a cache factory utility in you application in order to make caching
work. If you don't, ``node.ext.ldap`` falls back to use ``bda.cache.NullCache``,
which does not cache anything and is just an API placeholder.

To provide a cache based on ``Memcached`` install memcached server and
configure it. Then you need to provide the factory utility:

.. code-block:: pycon

    >>> from zope.interface import registry

    >>> components = registry.Components('comps')

    >>> from node.ext.ldap.cache import MemcachedProviderFactory

    >>> cache_factory = MemcachedProviderFactory()

    >>> components.registerUtility(cache_factory)

In case of multiple memcached backends on various IPs and ports initialization
of the factory looks like this:

.. code-block:: pycon

    >>> components = registry.Components('comps')

    >>> cache_factory = MemcachedProviderFactory(servers=[
    ...     '10.0.0.10:22122',
    ...     '10.0.0.11:22322'
    ... ])

    >>> components.registerUtility(cache_factory)


Dependencies
------------

- python-ldap

- passlib

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


Contributors
============

- Robert Niederreiter

- Florian Friesdorf

- Jens Klein

- Georg Bernhard

- Johannes Raggam

- Alexander Pilz

- Domen Kožar

- Daniel Widerin

- Asko Soukka

- Alex Milosz Sielicki

- Manuel Reinhardt

- Philip Bauer
