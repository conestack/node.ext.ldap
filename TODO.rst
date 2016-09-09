TODO
====

- define what our retry logic should look like, re-think function of session,
  communicator and connector. (check ldap.ldapobject.ReconnectLDAPObject)
  ideas: more complex retry logic with fallback servers, eg. try immediately
  again, if that fails use backup server, then start to probe other server
  after a timespan, report status of ldap servers, preferred server,
  equal servers, load balancing; Are there ldap load balancers to recommend?

- consider ``search_st`` with timeout.

- investigate ``ReconnectLDAPObject.set_cache_options``

- check/implement silent sort on only the keys ``LDAPNode.sortonkeys``

- node.ext.ldap.filter unicode/utf-8

- interactive configuration showing live how many users/groups are found with
  the current config and what a selected user/group would look like

- Configuration validation for UGM. Add some checks in ``Ugm.__init__`` which
  tries to block stupid configuration.

- group in group support

- rework ldap testsetup to allow for multiple servers in order to test with
  different overlays it would be nice to start different servers or have one
  server with multiple databases. whatever feels better.

- rework tests and ldifs to target isolated aspects

- potentially multi-valued attrs always as list!

