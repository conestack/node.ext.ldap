Overview
========

``node.ext.ldap`` is a LDAP convenience library for LDAP communication based on 
`python-ldap <http://pypi.python.org/pypi/python-ldap>`_ and
`node <http://pypi.python.org/pypi/node>`_.

The package contains base configuration and communication objects, a LDAP node
object and a LDAP node based user and group management implementation utilizing
`node.ext.ugm <http://pypi.python.org/pypi/node.ext.ugm>`_.


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


LDAPNode
--------

You can build and edit LDAP data trees with the ``LDAPNode`` which utilizes the
`node <http://pypi.python.org/pypi/node>`_ package.

The root Node expects the base DN and the server properties to initialize.::

    >> from node.ext.ldap import LDAPNode
    >> root = LDAPNode('dc=my-domain,dc=com', props=props)
    >> root.keys()
    ['ou=customers']

You can create and add new LDAP entries.::

    >> person = LDAPNode()
    >> person.attributes['objectClass'] = ['top', 'person']
    >> person.attributes['sn'] = 'Mustermann'
    >> person.attributes['cn'] = 'Max'
    >> person.attributes['description'] = 'Description'
    >> customers['cn=max'] = person
    >> customers.keys()
    ['cn=max']

On ``__call__`` the modifications of the tree are written to the directory.::

    >> customers()

Modification of entry attributes.::

    >> person.attributes['description'] = 'Another description'
    >> person()
    
    >> del person.attributes['description']
    >> person()

Deleting of entries.::

    >> del customers['cn=max']
    >> customers()

For more details see the corresponding source and test files.


Character Encoding
------------------

LDAP (v3 at least, `RFC 2251`_) uses utf8 string encoding. Since 1.5.1,
LDAPSession and LDAPNode translate these to unicodes for you. Consider it a
bug, if you receive anything else than unicode from LDAPSession or LDAPNode.
Everything below that LDAPConnector and LDAPCommunicator give you the real ldap
experience. - Should we change that, too?

Unicode strings you pass to nodes or sessions are automatically encoded to uft8
for LDAP. If you feed them normal strings they are decoded as utf8 and
reencoded as utf8 to make sure they are utf8 or compatible, e.g. ascii.

If decoding as utf8 fails, the value is assumed to be in binary and left as a
string (see TODO).

If you have an LDAP server that does not use utf8, monkey-patch
node.ext.ldap.CHARACTER_ENCODING.
XXX: this is dirty, make char encoding configurable a better way

If you are confused by all that encoding/decoding: python knows in what
encoding it stores its unicodes, however, it cannot know for normal strs.
Therefore, you should only use unicodes. In order to get a unicode for a str, a
string is decoded according to a given encoding schema (eg utf8). And encoding
a unicode produces a str in a specific encoding (eg utf8).

.. _`RFC 2251`: http://www.ietf.org/rfc/rfc2251.txt


Caching Support
---------------

``node.ext.ldap`` can cache LDAP searches using ``bda.cache``. You need 
to provide a cache factory utility in you application in order to make caching
work. If you don't, ``node.ext.ldap`` falls back to use ``NullCache``, which
does not cache anything and is just an API placeholder. 

To provide an cache based on ``Memcached`` install memcached server and
configure it. Then you need to provide the factory utility.::
    
    >> from node.ext.ldap.cache import MemcachedProviderFactory
    >> providerfactory = MemcachedProviderFactory()
    >> from zope.component import provideUtility
    >> provideUtility(providerfactory)
    
In the case of more than one memcached backend running or not running on
127.0.0.1 at default port, initialization of factory looks like::    

    >> providerfactory = MemcachedProviderFactory(servers=[10.0.0.10:22122,
    ...                                                     10.0.0.11:22322])
    >> provideUtility(providerfactory)


Dependencies
============

- python-ldap

- node

- bda.cache


Notes on python-ldap
====================

There are different compile issues on different platforms. If you experience
problems with ``python-ldap``, make sure it is available in the python
environment you run buildout in, so it won't be fetched and build by buildout
itself.


TODO
====

- TLS/SSL Support. in LDAPConnector
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

- check/implement silent sort on only the keys LDAPNode.sortonkeys()

- binary attributes: 1. introduce Binary: ``node['cn=foo'].attrs['image']
  = Binary(stream)``, 2. parse ldap schema to identify binary attributes, also
  further types like BOOL

- node.ext.ldap.filter unicode/utf-8

- auto-detection of rdn attribute (semi closed)

- interactive configuration showing life how many users/groups are found with
  the current config and how a selected user/group would look like


Changes
=======

0.9dev
------

- refactor form bda.ldap. 


Contributors
============

- Robert Niederreiter <rnix@squarewave.at>

- Florian Friesdorf <flo@chaoflow.net>

- Jens Klein <jens@bluedynamics.com>

- Georg Bernhard <g.bernhard@akbild.ac.at>

- Johannes Raggam <johannes@bluedynamics.com>
