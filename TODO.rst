TODO
====

- consider ``search_st`` with timeout.

- investigate ``ReconnectLDAPObject.set_cache_options``.

- check/implement silent sort on only the keys ``LDAPNode.sortonkeys``.

- interactive configuration showing live how many users/groups are found with
  the current config and what a selected user/group would look like.

- Configuration validation for UGM. Add some checks in ``Ugm.__init__`` which
  tries to block stupid configuration.

- group in group support.

- rework ldap testsetup to allow for multiple servers in order to test with
  different overlays it would be nice to start different servers or have one
  server with multiple databases. whatever feels better.

- rework tests and ldifs to target isolated aspects.

- potentially multi-valued attrs always as list.

