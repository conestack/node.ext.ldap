LDAP
====

LDAP in general
---------------

ldap is hierarhical, every node is uniquely identified via a
distinguished name (dn) and every node can be a leave or the root (base)
for another subtree. Among siblings a leave is uniquely identified by
the relative distinguished name (rdn). In general an rdn looks like
``<attr_name>=<attr_value>``, but may also be composed of multiple such
pairs joined by '+'.::

    # base of all bases, also named base dn
    dn: dc=my-domain,dc=com
    objectClass: top 
    objectClass: dcObject
    objectClass: organization
    o: my-organization
    dc: my-domain

    dn: ou=customers,dc=my-domain,dc=com
    ou: customers
    objectClass: top 
    objectClass: organizationalUnit

    dn: ou=customer1,ou=customers,dc=my-domain,dc=com
    ou: customer1
    objectClass: top 
    objectClass: organizationalUnit

    dn: ou=customer2,ou=customers,dc=my-domain,dc=com
    ou: customer2
    objectClass: top 
    objectClass: organizationalUnit

In Zope/Plone terminology every node is a container that has attributes
and child nodes. objectclasses define what attributes a node must and
may have, similar to zope schema interfaces. objectclasses supplement
(subclass) other objectclasses, the root of all being ``top``.

LDAP Schema (in contrast to zope schemas) define what objectClasses and
attributetypes an ldap server knows about, attributetypes define valid
values for attributes, whether they are case sensitive, binary, how
values are compared, ... .

To search an ldap directory, you specify a baseDN, scope and filter
- baseDN, where to start the search
- scope, how far to go, BASE (only the baseDN itself), ONELEVEL (direct child
  nodes of the baseDN), SUBTREE (everything beneath the baseDN)
- filter, what nodes to match, the default is '(objectClass=*)', which matches
  all nodes (more on this below)

Recent LDAP implementations all support querying the known schemas via ldap,
they could be used and translated to zope schemas.


LDAP Users
----------

In order for a node to qualify as an ldap user, it only needs to have a
``userPassword`` attribute. The username is the dn, and the password hash is
stored as the ``userPassword`` attribute value. As the password is hashed, in
order to authenticate a user the dn and plain-text password are passed to
``bind(userdn, password)``.

A user can be anywhere in the ldap tree. In order to produce a listing of
valid users, sane ldap layouts use a dedicated objectClass to identify users,
e.g. inetOrgPerson. The existence of a userPassword attribute does not suffice,
as pure system accounts, e.g. the manager dn for the ldap directory also has
one.

ActiveDirectory, being in my personal opinion on the border of sane
implementations, to say the best, has an ``objectClass: computer`` that
supplements ``user``, i.e. all computers are users. If you combine that with
two logon domains in one ActiveDirectory, the filters get really messy.
However, they have objectCategory and there is normally a group of which all
real users are members.


LDAP Groups
-----------

There are (at least) three concepts to model groups in ldap.

1. dedicated node, ``objectClass: groupOfNames`` (openldap), all information on
   the group node, the user node does not store information, user node is
   arbitrary::

   dn: cn=group1,dc=my-domain,dc=com
   cn: group1
   objectClass: top
   objectClass: groupOfNames
   member: <dn of user or group (even an arbitrary node?)>
   member: <dn of user or group (even an arbitrary node?)>
   member: <dn of user or group (even an arbitrary node?)>

2. mixture, ``objectClass: posixGroup`` (OpenDirectory and openldap nis.schema),
   membership information on the user node, group name on the group node, only
   user nodes with ``objectClass: posixAccount``::

   dn: cn=group2,dc=my-domain,dc=com
   cn: group2
   objectClass: top
   objectClass: posixGroup
   gidNumber: 42

   dn: uid=user1,dc=my-domain,dc=com
   uid: user1
   objectClass: top
   objectClass: posixAccount
   uidNumber: 17
   gidNumber: 42
   homeDirectory: /home/user1

Note: The schemas do not define which attribute is used for the RDN, it is up
to the ldap directory layout, the only condition is: it must be unique among
its siblings.

Note: At least for openldap nis schema the homeDirectory is required, I just
put it there so I can use those entries later on for testing.

3. redundant, ``objectClass: group`` (ActiveDirectory), membership information
   on the group and on the user::

   dn: cn=group3,dc=my-domain,dc=com
   cn: group3
   objectClass: top
   objectClass: group
   member: <dn of user or group (even an arbitrary node?)>
   member: <dn of user or group (even an arbitrary node?)>
   member: <dn of user or group (even an arbitrary node?)>

   dn: cn=user2,dc=my-domain,dc=com
   cn: user2
   objectClass: top
   objectClass: person
   objectClass: organizationalPerson
   objectClass: user
   memberOf: cn=group3,dc=my-domain,dc=com

All have in common that a group can be anywhere in ldap tree. But in general
they can be uniquely identified by objectClass.

For further reading: http://www.zytrax.com/books/ldap/
