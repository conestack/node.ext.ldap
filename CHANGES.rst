History
=======

1.0rc1 (2021-11-08)
-------------------

- Rename deprecated ``allow_non_node_childs`` to ``allow_non_node_children``
  on ``PrincipalAliasedAttributes``.
  [rnix]

- Allow to generate MD5 hashes in FIPS enabled environments.
  [frapell]

- Fix DN comparison in ``LDAPStorage.node_by_dn`` to ignore case sensitivity.
  [rnix]


1.0b12 (2020-05-28)
-------------------

- Make sure ``LDAPPrincipals._login_attr`` has a value. This way
  ``LDAPUsers.id_for_login`` always returns the principal id as stored in the
  database.
  [rnix]

- Improve value comparison in ``LDAPAttributesBehavior.__setitem__`` to avoid
  unicode warnings.
  [rnix]

- Implement ``invalidate`` on ``node.ext.ldap.ugm._api.Ugm``.
  [rnix]

- Support for group DNs in ``memberOf`` attribute that are outside of the UGMs configured group.
  [jensens]


1.0b11 (2019-09-08)
-------------------

- Return empty search result list when an LDAP error occurs.
  Fixes `issue #50 <https://github.com/conestack/node.ext.ldap/issues/50>`_.
  [maurits]

- Skip objects that were found in LDAP while searching on several attributes but don't contain the required attribute.
  [fredvd, maurits]


1.0b10 (2019-06-30)
-------------------

- Fix cache key generation.
  [rnix, pbauer]


1.0b9 (2019-05-07)
------------------

- Refactor mapping from object-class to format and attributes to increase readability.
  [jensens]

- Increase Exception verbosity to ease debugging.
  [jensens]

- Add missing object classes from principal config when persisting principals.
  [rnix]

- Remove attribute from entry if setting it's value to ``node.utils.UNSET`` or
  empty string. Most LDAP implementations not allow setting empty values, thus
  we delete the entire attribute in this case.
  [rnix]

- Add debug-level logging if search fails with no-such-object.
  [jensens]

- Fix problem with missing LDAP batching cookie in search.
  [jensens, rnix]

- Remove ``smbpasswd`` dependency. Use ``passlib`` instead.
  [rnix]

- Use ``bytes_mode=False`` when using ``python-ldap``. This is the default
  behavior in python 3 and handles everything as unicode/text except
  entry attribute values.
  For more details see https://www.python-ldap.org/en/latest/bytes_mode.html
  [rnix]

- Add ``ensure_bytes_py2`` in ``node.ext.ldap.base``.
  [rnix]

- Rename ``decode_utf8`` to ``ensure_text`` in ``node.ext.ldap.base``.
  [rnix]

- Rename ``encode_utf8`` to ``ensure_bytes`` in ``node.ext.ldap.base``.
  [rnix]

- Python 3 Support.
  [rnix, reinhardt]

- Convert doctests to unittests.
  [rnix]


1.0b8 (2018-10-22)
------------------

- Use ``ldap.ldapobject.ReconnectLDAPObject`` instead of ``SimpleLDAPObject`` to create
  the connection object. This makes the connection more robust.
  Add properties `retry_max` (default 1) and `retry_delay` (default 10) to
  ``node.ext.ldap.properties.LDAPServerProperties`` to configure ``ReconnectLDAPObject``.
  [joka]

- Use ``explode_dn`` in ``LDAPPrincipals.__getitem__`` to prevent ``KeyError``
  if DN contains comma.
  [dmunicio]


1.0b7 (2017-12-15)
------------------

- Do not catch ``ValueError`` in
  ``node.ext.ldap._node.LDAPStorage.batched_search``.
  [rnix]

- Use property decorators for ``node.ext.ldap._node.LDAPStorage.changed``
  and ``node.ext.ldap.session.LDAPSession.baseDN``.
  [rnix]

- Fix signature of ``node.ext.ldap.interfaces.ILDAPStorage.search`` to match
  the actual implementation in ``node.ext.ldap._node.LDAPStorage.search``.
  [rnix]

- Fix signature of ``node.ext.ldap.ugm.LDAPPrincipals.search`` according to
  ``node.ext.ugm.interfaces.IPrincipals.search``. The implementation exposed
  LDAP related arguments and has been renamed to ``raw_search``.
  [rnix]

- Add ``exists`` property to ``LDAPStorage``.
  [rnix]

- Add ``objectSid`` and ``objectGUID`` from Active Directory schema to
  ``properties.BINARY_DEFAULTS``.
  [rnix]

- Fix default value of ``LDAPStorage._multivalued_attributes`` and
  ``LDAPStorage._binary_attributes``.
  [rnix]


1.0b6 (2017-10-27)
------------------

- Switch to use mdb as default db for slapd i testing layer.
  [jensens]

- fix tests, where output order could be random.
  [jensens]


1.0b5 (2017-10-27)
------------------

- make db-type in test layer configurable
  [jensens]


1.0b4 (2017-06-07)
------------------

- Turning referrals off to fix problems with MS AD if it contains aliases.
  [alexsielicki]

- Fix search to check list of binary attributes directly from the root node
  data (not from attr behavior) to avoid unnecessarily initializing attribute
  behavior just a simple search
  [datakurre]

- Fix to skip group DNs outside the base DN to allow users' memberOf
  attribute contain groups outside the group base DN
  [datakurre]


1.0b3 (2016-10-18)
------------------

- Add a ``batched_search`` generator function, which do the actual batching for us.
  Use this function internally too.
  [jensens, rnix]

- In testing set size_limit to 3 in ``slapd.conf`` in order to catch problems with batching.
  [jensens, rnix]

- Fix missing paging in UGM group mapping method ``member_ids``.
  [jensens]


1.0b2 (2016-09-09)
------------------

- Minor code cleanup
  [jensens]

- Paginate LDAP node ``__iter__``.
  [jensens, rnix]


1.0b1 (31.12.2015)
------------------

- Remove ``ILDAPProps.check_duplicates`` respective
  ``LDAPProps.check_duplicates``.
  [rnix]

- ``rdn`` can be queried via ``attrlist`` in ``LDAPNode.search`` explicitely.
  [rnix]

- Introduce ``get_nodes`` keyword argument in ``LDAPNode.search``. When set,
  search result contains ``LDAPNode`` instances instead of DN's in result.
  [rnix]

- ``LDAPNode.search`` returns DN's instead of RDN's in result. This fixes
  searches with scope SUBTREE where result items can potentially contain
  duplicate RDN's.
  [rnix]

- Introduce ``node_by_dn`` on ``LDAPNode``.
  [rnix]

- remove bbb code: no python 2.4 support (2.7+ now), usage of LDAPProperties
  mandatory now.
  [jensens]

- Overhaul LDAP UGM implementation.
  [rnix]

- LDAP Node only returns direct children in ``__iter__``, even if search
  scope subtree.
  [rnix]

- LDAPNode keys cannot be aliased any longer. Removed ``_key_attr`` and
  ``_rdn_attr``.
  child.

- LDAPNode does not provide secondary keys any longer. Removed
  ``_seckey_attrs``.
  [rnix]

- Deprecate ``node.ext.ldap._node.AttributesBehavior`` in favor of
  ``node.ext.ldap._node.LDAPAttributesBehavior``.
  [rnix]

- Remove deprecated ``node.ext.ldap._node.AttributesPart``.
  [rnix]

- Don't fail on ``UNWILLING_TO_PERFORM`` exceptions when authenticating. That
  might be thrown, if the LDAP server disallows us to authenticate an ``admin``
  user, while we are interested in the local ``admin`` user.
  [thet]

- Add ``ignore_cert`` option to ignore TLS/SSL certificate errors for self
  signed certificates when using the ``ldaps`` uri schema.
  [thet]

- Housekeeping.
  [rnix]


0.9.7
-----

- Added possibility to hook external LDIF layer for testldap server via
  buildout configuration.
  [rnix]

- Update openldap version in buildout configs.
  [rnix]


0.9.6
-----

- Add new property to allow disable ``check_duplicates``.
  This avoids following Exception when connecting ldap servers with
  non-unique attributes used as keys.  [saily]
  ::

    Traceback (most recent call last):
    ...
    RuntimeError: Key not unique: <key>='<value>'.

- ensure attrlist values are strings
  [rnix, 2013-12-03]


0.9.5
-----

- Add ``expired`` property to ``node.ext.ldap.ugm._api.LDAPUser``.
  [rnix, 2012-12-17]

- Introduce ``node.ext.ldap.ugm._api.calculate_expired`` helper function.
  [rnix, 2012-12-17]

- Lookup ``expired`` attribut from LDAP in
  ``node.ext.ldap.ugm._api.LDAPUser.authenticate``.
  [rnix, 2012-12-17]


0.9.4
-----

- Encode DN in ``node.ext.ldap._node.LDAPStorage._ldap_modify``.
  [rnix, 2012-11-08]

- Encode DN in ``node.ext.ldap._node.LDAPStorage._ldap_delete``.
  [rnix, 2012-11-08]

- Encode DN in ``node.ext.ldap.ugm._api.LDAPUsers.passwd``.
  [rnix, 2012-11-08]

- Encode DN in ``node.ext.ldap.ugm._api.LDAPUsers.authenticate``.
  [rnix, 2012-11-07]

- Encode ``baseDN`` in ``LDAPPrincipal.member_of_attr``.
  [rnix, 2012-11-06]

- Encode ``baseDN`` in ``AttributesBehavior.load``.
  [rnix, 2012-11-06]

- Python 2.7 compatibility.
  [rnix, 2012-10-16]

- PEP-8.
  [rnix, 2012-10-16]

- Fix ``LDAPPrincipals.idbydn`` handling UTF-8 DN's properly.
  [rnix, 2012-10-16]

- Rename parts to behaviors.
  [rnix, 2012-07-29]

- adopt to ``node`` 0.9.8.
  [rnix, 2012-07-29]

- Adopt to ``plumber`` 1.2.
  [rnix, 2012-07-29]

- Do not convert cookie to unicode in ``LDAPSession.search``. Cookie value is
  no utf-8 string but octet string as described in
  http://tools.ietf.org/html/rfc2696.html.
  [rnix, 2012-07-27]

- Add ``User.group_ids``.
  [rnix, 2012-07-26]


0.9.3
-----

- Fix schema to not bind to test BaseDN only and make binding deferred.
  [jensens, 2012-05-30]


0.9.2
-----

- Remove ``escape_queries`` property from
  ``node.ext.ldap.properties.LDAPProps``.
  [rnix, 2012-05-18]

- Use ``zope.interface.implementer`` instead of ``zope.interface.implements``.
  [rnix, 2012-05-18]

- Structural object class ``inetOrgPerson`` instead of ``account`` on posix
  users and groups related test LDIF's
  [rnix, 2012-04-23]

- session no longer magically decodes everything and prevents binary data from
  being fetched from ldap. LDAP-Node has semantic knowledge to determine binary
  data LDAP-Node converts all non binary data and all keys to unicode.
  [jensens, 2012-04-04]

- or_values and or_keys for finer control of filter criteria
  [iElectric, chaoflow, 2012-03-24]

- support paged searching
  [iElectric, chaoflow, 2012-03-24]


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

