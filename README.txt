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
============

  * python-ldap
  * bda.cache


TODO
====

  * TLS/SSL Support. in LDAPConnector
  * Improve retry logic in LDAPSession
  * Extend LDAPSession object to handle Fallback server(s)
  * Tests


Copyright
=========

Copyright (c) 2006-2009: BlueDynamics Alliance, Austria


Credits
=======

  * Robert Niederreiter <rnix@squarewave.at>
  * Jens Klein <jens@bluedynamics.com>
  * Georg Bernhard <g.bernhard@akbild.ac.at>
  * Florian Friesdorf <flo@chaoflow.net>
  * Johannes Raggam <johannes@bluedynamics.com>
