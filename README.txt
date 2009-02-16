LDAP convenience library with caching support
=============================================

This Package provides objects for LDAP communication. You probably be
interrested in the LDAPSession object.

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
when instanciating the properties obeject.

  >>> props = LDAPServerProperties('localhost',
  ...                              389,
  ...                              'cn=user,dc=example,dc=com',
  ...                              'secret',
  ...                              cache=False)


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
  * Convenience for modification calls refering to adding modifying and deleting
    attributes.

Changes
-------

  * 1.2.3 (rnix, 2009-02-11)
    * bugfix in ``LDAPSession``. pass ``force_reload`` to relevant execution
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
