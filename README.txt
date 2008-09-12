========
bda.ldap
========

Overview
========

This Package provides objects for LDAP communication. You probably be
interrested in the LDAPSession object.

LDAP Queries are cached by default.
- Depends on plone.memoize
- Adjust CACHE_TIMEOUT_SECONDS for to control cache-time
- If you don't want LDAP Caching, disable the ldapcached import in base.py


Dependencies
============

python-ldap


TODO
====

- Improve retry logic in LDAPSession
  
- Extend LDAPSession object to handle Fallback server(s)


Copyright
=========

Copyright (c) 2006-2008: BlueDynamics Alliance, Austria


Credits
=======

- Robert Niederreiter <rnix@squarewave.at
  
- Jens Klein <jens@bluedynamics.com>
  
- Georg Bernhard <g.bernhard@akbild.ac.at>
  
- Florian Friesdorf <flo@chaoflow.net>

- Johannes Raggam <johannes@bluedynamics.com>
