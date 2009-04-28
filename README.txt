
LDAP convenience library with caching support
=============================================

This Package provides objects for LDAP communication.

You can work with the LDAPSession object.:

  >>> from bda.ldap.base import ONELEVEL
  >>> from bda.ldap.session import LDAPSession
  >>> from bda.ldap.properties import LDAPServerProperties
  
  >>> props = LDAPServerProperties('localhost',
  ...                              389,
  ...                              'cn=user,dc=example,dc=com',
  ...                              'secret')
  >>> session = LDAPSession(props)
  >>> res = session.search('(uid=*)', ONELEVEL)

LDAP Queries are cached by default. You can disable this via ``cache`` kw arg
when instanciating the properties obeject.:

  >>> props = LDAPServerProperties('localhost',
  ...                              389,
  ...                              'cn=user,dc=example,dc=com',
  ...                              'secret',
  ...                              cache=False)

Since version 1.3 there exists an LDAPNode object, which behaves mostly like a
dictionary and is the prefered method to access and modify the tree.

The root Node expects the base DN and the server properties to initialize.:

  >>> root = LDAPNode('dc=my-domain,dc=com', props=props)
  >>> root.keys()
  ['ou=customers']

You can create and add new LDAP entries:

  >>> person = LDAPNode()
  >>> person.attributes['objectClass'] = ['top', 'person']
  >>> person.attributes['sn'] = 'Mustermann'
  >>> person.attributes['cn'] = 'Max'
  >>> person.attributes['description'] = 'Description'
  >>> customers['cn=max'] = person
  >>> customers.keys()
  ['cn=max']

On ``__call__`` the modifications of the tree are written to the directory.:

  >>> customers()

Modification of entry attributes.:

  >>> person.attributes['description'] = 'Another description'
  >>> person()

  >>> del person.attributes['description']
  >>> person()

Deleting of entries.:

  >>> del customers['cn=max']
  >>> customers()

For more details see the corresponding source and test files.

Dependencies
------------

  * python-ldap
  * bda.cache

Notes on python-ldap
--------------------

  Although python-ldap is available via pypi, we excluded it from
  ``install_requires`` due to different compile issues on different
  platforms.
  
  So you have to make sure that ``pyhon-ldap`` is available on your system in
  any way.

TODO
----

  * TLS/SSL Support. in LDAPConnector
  * Improve retry logic in LDAPSession
  * Extend LDAPSession object to handle Fallback server(s)
  * Modification bug if cache is enabled

Changes
-------

  * 1.3 (rnix, 2009-04-16)
    * support ``attrlist`` and ``attrsonly`` for search functions
    * add LDAPEntry object
    * add search base to cache key

  * 1.2.3 (rnix, 2009-02-11)
    * bugfix in ``LDAPSession``. Pass ``force_reload`` to relevant execution
      function

  * 1.2.2 (rnix, jensens - 2009-02-11)
    * add buildout for standalone testing
    * add tests
    * provide relevant objects via package ``__init__``

  * 1.2.1 (rnix - 2009-02-10)
    * provide same ``search()`` signature in ``LDAPSession`` as
      in ``LDAPCommunicator``
    * log only on debug

  * <= 1.2 (all contributors)
    * make it work


Copyright
---------

Copyright (c) 2006-2009: BlueDynamics Alliance, Austria


Credits
-------

  * Robert Niederreiter <rnix@squarewave.at>
  * Jens Klein <jens@bluedynamics.com>
  * Georg Bernhard <g.bernhard@akbild.ac.at>
  * Florian Friesdorf <flo@chaoflow.net>
  * Johannes Raggam <johannes@bluedynamics.com>
