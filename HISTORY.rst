
Changes
=======

0.9.1
-----

- added is_multivalued to properties and modified node to use this list instead
  of the static list. prepare for binary attributes.
  [jensens, 2012-03-19]

- added schema_info to node.
  [jensens, 2012-03-19]

- ``shadowInactive`` defaults to ``0``.
  [rnix, 2012-03-06]

- Introduce ``expiresAttr`` and ``expiresUnit`` in principals config.
  Considered in ``Users.authenticate``.
  [rnix, 2012-02-11]

- Do not throw ``KeyError`` if secondary key set but attribute not found on
  entry. In case, skip entry.
  [rnix, 2012-02-10] 

- Force unicode ids and keys in UGM API.
  [rnix, 2012-01-23]

- Add unicode support for filters.
  [rnix, 2012-01-23]

- Add ``LDAPUsers.id_for_login``.
  [rnix, 2012-01-18]

- Implement memberOf Support for openldap memberof overlay and AD memberOf
  behavior.
  [rnix, 2011-11-07]

- Add ``LDAPProps.escape_queries`` for ActiveDirectory.
  [rnix, 2011-11-06]

- Add group object class to member attribute mapping for ActiveDirectory.
  [rnix, 2011-11-06]

- Make testlayer and testldap more flexible for usage outside this package.
  [jensens, 2010-09-30]

0.9
---

- refactor form ``bda.ldap``.
  [rnix, chaoflow]

