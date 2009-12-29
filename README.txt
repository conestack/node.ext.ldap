LDAP convenience library with caching support
=============================================

This Package provides objects for LDAP communication.

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

You can build and edit LDAP data trees with the ``LDAPNode`` object.

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

Dependencies
------------

- python-ldap

- bda.cache

Notes on python-ldap
--------------------

Although python-ldap is available via pypi, we excluded it from
``install_requires`` due to different compile issues on different platforms.

So you have to make sure that ``pyhon-ldap`` is available on your system in
any way.

TODO
----

- TLS/SSL Support. in LDAPConnector

- Improve retry logic in LDAPSession

- Extend LDAPSession object to handle Fallback server(s)

Changes
=======

1.4.1
-----

- Add read property ``ldap_session`` to ``LDAPNode``. This way its clean to take  
  the session of ``LDAPNode`` in an application i.e. for searching. Be careful 
  while using the session directly to manipulate the LDAP; responsibility to 
  invalidate the ``LDAPNode`` instances is on the application developer.

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
