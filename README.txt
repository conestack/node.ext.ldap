LDAP convenience library
========================

This Package provides objects for LDAP communication. 

LDAP Session
------------

You can work with the ``LDAPSession`` object.
::

    >>> from bda.ldap import ONELEVEL
    >>> from bda.ldap import LDAPSession
    >>> from bda.ldap import LDAPProps
    
    >>> props = LDAPProps('localhost',
    ...                   389,
    ...                   'cn=user,dc=example,dc=com',
    ...                   'secret'
    ...                   cache=True,
    ...                   timeout=12345)
    >>> session = LDAPSession(props)
    >>> res = session.search('(uid=*)', ONELEVEL)
    
LDAP Node
---------

You can build and edit LDAP data trees with the ``LDAPNode`` which is based on 
``zodict.Node``. 

The root Node expects the base DN and the server properties to initialize.
::

    >>> from bda.ldap import LDAPNode
    >>> root = LDAPNode('dc=my-domain,dc=com', props=props)
    >>> root.keys()
    ['ou=customers']

You can create and add new LDAP entries.
::

    >>> person = LDAPNode()
    >>> person.attributes['objectClass'] = ['top', 'person']
    >>> person.attributes['sn'] = 'Mustermann'
    >>> person.attributes['cn'] = 'Max'
    >>> person.attributes['description'] = 'Description'
    >>> customers['cn=max'] = person
    >>> customers.keys()
    ['cn=max']

On ``__call__`` the modifications of the tree are written to the directory.
::

    >>> customers()

Modification of entry attributes.
::

    >>> person.attributes['description'] = 'Another description'
    >>> person()
    
    >>> del person.attributes['description']
    >>> person()

Deleting of entries.
::

    >>> del customers['cn=max']
    >>> customers()

For more details see the corresponding source and test files.

Caching Support
---------------

``bda.ldap`` caches LDAP searches using the lightweight ``bda.cache``. You need 
to provide a utility in you application in order to make caching work. If you
dont, ``bda.ldap`` falls back to use the NullCache, which does not cache 
anything. 

To provide an cache based on ``Memcached`` install the memcached server,  
configure and start it. I suppose its started on localhost port 11211 (which is 
a common default). Then you need to provide a utility acting as a factory.  
::
    
    >>> from bda.ldap.cache import MemcachedProviderFactory
    >>> providerfactory = MemcachedProviderFactory()
    >>> from zope.component import provideUtility
    >>> provideUtility(providerfactory)
    
In the case you have more than one memcached server running or hav it running on 
another maschine, you need to initialize the factory different::    

    >>> providerfactory = MemcachedProviderFactory(servers=[10.0.0.10:22122,
    ...                                                     10.0.0.11:22322])
    >>> provideUtility(providerfactory)

Dependencies
============

- python-ldap

- zodict

- bda.cache


Notes on python-ldap
====================

Although python-ldap is available via pypi, we excluded it from
``install_requires`` due to different compile issues on different platforms.

So you have to make sure that ``pyhon-ldap`` is available on your system in
any way.

TODO
====

- TLS/SSL Support. in LDAPConnector
  could be useful, python-ldap's
    class SmartLDAPObject(ReconnectLDAPObject)
     |  Mainly the __init__() method does some smarter things
     |  like negotiating the LDAP protocol version and calling
     |  LDAPObject.start_tls_s().


- Improve retry logic in LDAPSession
  could be useful, python-ldap's
    class ReconnectLDAPObject(SimpleLDAPObject)
     |  In case of server failure (ldap.SERVER_DOWN) the implementations
     |  of all synchronous operation methods (search_s() etc.) are doing
     |  an automatic reconnect and rebind and will retry the very same
     |  operation.

- Extend LDAPSession object to handle Fallback server(s)

Changes
=======

1.5.1 unreleased
----------------

- added support for sort to node. Note: This wakes up all children of Node.
  (jensens, 2010-04-16) 

- added support for "items() to Node".
  (jensens, 2010-04-16) 

- BBB compatibility for zope2.9
  (rnix, jensens, 2010-02-17)

- If a Node was added and no child added __iter__ failed. Fixed now.
  (jensens, 2010-01-19) 

- If a Node was added we cant load its attributes. Takes this into account now.
  (jensens, 2010-01-17) 

1.5.0
-----

- Made ``MemcachedProviderFactory`` configureable. Defaults behave like in prior
  versions. New: We can pass ``server=`` keyword argument to the 
  constructor expecting a list of servers, each in the form *server:port*.
  (jensens, 2009-12-30)

- Dont provide any cache provider factory by default. Added a 
  ``nullCacheProviderFactory`` which  provides a non-caching behaviour. Use this
  as fallback if no utility was registered.   
  (jensens, 2009-12-30)

- Add read property ``ldap_session`` to ``LDAPNode``. This way its clean to take  
  the session of ``LDAPNode`` in an application i.e. for searching. Be careful 
  while using the session directly to manipulate the LDAP; responsibility to 
  invalidate the ``LDAPNode`` instances is on the application developer.
  (jensens, 2009-12-30)

1.4.0
-----

- Add ``LDAPProps`` object. Its points to ``LDAPServerProperties`` class. The
  latter one will be renamed to ``LDAPProps`` in version 1.5. Too long class
  name. (rnix, 2009-12-23)

- Add ``LDAPSession.unbind`` function. (rnix, 2009-12-23)

- Add some tests for ``LDAPSession``. (rnix, 2009-12-23)

- Remove deprecated ``cache`` kwarg from ``LDAPSession.__init__.``. Cache
  timeout and flag if cache is enabled is done due to ``LDAPServerProperties``.
  (rnix, 2009-12-23)

- Deprecate Signature of ``LDAPConnector.__init__``. (rnix, 2009-12-23)

- Deprecate ``LDAPConnector.setProtocol``, ``LDAPCommunicator.setBaseDN``,
  ``LDAPCommunicator.getBaseDN``, ``LDAPSession.setBaseDN``. (rnix, 2009-12-23)
  
- Refactor the whole ``LDAPNode`` to use ``zodict.LifecycleNode``. Clean up of
  the ``LDAPNode`` code. (jensens, rnix, 2009-12-22)

- improved stop mechanism of ldap server in tests (jensens, 2009-12-16)

- remove deprecation warning: use `hashlib` for md5 and fallback to `md5`  
  with python2.4. (jensens, 2009-12-16)

1.3.2
-----

- handle timeout of cache, workaround atm (rnix, 2009-09-02)

1.3.1
-----

- add ``cache`` property to ``LDAPProperties``. (rnix, 2009-05-08)

- modify session to fit this new cache property. (rnix, 2009-05-07)

- add ``queryNode`` function. (rnix, 2009-05-07)

- add ``get`` function to node, this failed due LDAP read logic.
  (rnix, 2009-05-07)

1.3
---

- support ``attrlist`` and ``attrsonly`` for search functions.
  (rnix, 2009-04-16)

- add LDAPEntry object. (rnix, 2009-04-16)

- add search base to cache key. (rnix, 2009-04-16)

1.2.3
-----

- bugfix in ``LDAPSession``. Pass ``force_reload`` to relevant execution
  function. (rnix, 2009-02-11)

1.2.2
-----

- add buildout for standalone testing. (rnix, jensens - 2009-02-11)

- add tests. (rnix, jensens - 2009-02-11)

- provide relevant objects via package ``__init__``.
  (rnix, jensens - 2009-02-11)

1.2.1
-----

- provide same ``search()`` signature in ``LDAPSession`` as
  in ``LDAPCommunicator``. (rnix - 2009-02-10)
  
- log only on debug. (rnix - 2009-02-10)

<= 1.2
------

- make it work. 
  (all contributors)

Copyright
=========

Copyright (c) 2006-2009: BlueDynamics Alliance, Austria

Credits
=======

- Robert Niederreiter <rnix@squarewave.at>

- Jens Klein <jens@bluedynamics.com>

- Georg Bernhard <g.bernhard@akbild.ac.at>

- Florian Friesdorf <flo@chaoflow.net>

- Johannes Raggam <johannes@bluedynamics.com>
