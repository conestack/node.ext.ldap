#!/usr/bin/env python

import sys

container_template = """\
dn: ou=%(ou)s,dc=my-domain,dc=com
objectClass: top
objectClass: organizationalUnit
ou: %(ou)s
"""

user_template = """\
dn: uid=%(uid)s,ou=%(ou)s,dc=my-domain,dc=com
objectClass: inetOrgPerson
uid: %(uid)s
cn: %(cn)s
mail: %(mail)s
sn: %(sn)s
userPassword: %(password)s

"""

ou = sys.argv.pop(1)
n = int(sys.argv.pop(1))


print container_template % dict(ou=ou)
for x in range(n):
    print user_template % dict(
            uid='uid%d' % x,
            cn='cn%d' % x,
            mail='uid%d@%s' % (x, ou),
            ou=ou,
            password='secret%d' % x,
            sn='sn%d' % x,
            ),
