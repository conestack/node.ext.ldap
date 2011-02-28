#!/usr/bin/env python

import sys

base = "ou=groupOfNames_%(nusers)s_%(ngroups)s,dc=my-domain,dc=com"
domain = "groupOfNames_%(nusers)s_%(ngroups)s.com"

base_template = """\
dn: %(base)s
ou: groupOfNames_%(nusers)s_%(ngroups)s
objectClass: organizationalUnit
"""

users_template = """\
dn: ou=users,%(base)s
ou: users
objectClass: organizationalUnit
"""

users_add_template = """\
dn: ou=add,ou=users,%(base)s
ou: add
objectClass: organizationalUnit
"""

groups_template = """\
dn: ou=groups,%(base)s
ou: groups
objectClass: organizationalUnit
"""

groups_add_template = """\
dn: ou=add,ou=groups,%(base)s
ou: add
objectClass: organizationalUnit
"""

user_template = """\
dn: uid=uid%(n)s,ou=users,%(base)s
uid: uid%(n)s
objectClass: inetOrgPerson
cn: cn%(n)s
mail: uid%(n)s@%(domain)s
sn: sn%(n)s
userPassword: secret%(n)s
"""

group_template = """\
dn: cn=group%(n)s,ou=groups,%(base)s
cn: group%(n)s
objectClass: groupOfNames
member: cn=nobody
"""

member_template = "member: uid=uid%(n)s,ou=users,%(base)s"

nusers = int(sys.argv.pop(1))
ngroups = int(sys.argv.pop(1))

base = base % dict(nusers=nusers, ngroups=ngroups)
domain = domain % dict(nusers=nusers, ngroups=ngroups)

if len(sys.argv) > 1 and sys.argv[-1] == "add":
    print users_add_template % dict(base=base)
    print groups_add_template % dict(base=base)
    exit(0)

print base_template % dict(base=base, nusers=nusers, ngroups=ngroups)
print users_template % dict(base=base)
print groups_template % dict(base=base)

for nu in range(nusers):
    print user_template % dict(
        base=base,
        domain=domain,
        n=nu,
        )

for ng in range(ngroups):
    print group_template % dict(
        base=base,
        n=ng,
        ),
    for nu in range(ng):
        print member_template % dict(base=base, n=nu+1)
    print
