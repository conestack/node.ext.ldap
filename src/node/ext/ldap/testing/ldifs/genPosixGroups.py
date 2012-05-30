#!/usr/bin/env python

import sys

base = "ou=posixGroups_%(nusers)s_%(ngroups)s,dc=my-domain,dc=com"
domain = "posixGroups_%(nusers)s_%(ngroups)s.com"

base_template = """\
dn: %(base)s
ou: posixGroups_%(nusers)s_%(ngroups)s
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
cn: cn%(n)s
sn: sn%(n)s
objectClass: person
objectClass: posixAccount
objectClass: top
objectClass: shadowAccount
loginShell: /bin/bash
homeDirectory: /home/uid%(n)s
shadowFlag: 0
shadowMin: 0
shadowMax: 99999
shadowWarning: 0
shadowInactive: 99999
shadowExpire: 99999
userPassword: secret%(n)s
uidNumber: %(uid_num)i
gidNumber: %(gid_num)i
"""

group_template = """\
dn: cn=group%(n)s,ou=groups,%(base)s
cn: group%(n)s
gidNumber: %(gid_num)i
objectClass: posixGroup
objectClass: top
memberUid: nobody
"""

member_template = "memberUid: uid%(n)s"

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
        uid_num=nu,
        gid_num=nu,
        ),
    print

for ng in range(ngroups):
    print group_template % dict(
        base=base,
        n=ng,
        gid_num=ng,
        ),
    for nu in range(ng+1):
        print member_template % dict(n=nu)
    print
