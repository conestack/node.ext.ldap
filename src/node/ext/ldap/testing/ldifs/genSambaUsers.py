#!/usr/bin/env python

import sys
import smbpasswd

container_template = """\
dn: ou=sambaUsers,dc=my-domain,dc=com
objectClass: top
objectClass: organizationalUnit
ou: %(ou)s
"""

user_template = """\
dn: uid=%(uid)s,ou=sambaUsers,dc=my-domain,dc=com
objectClass: account
objectClass: top
objectClass: sambaSamAccount
uid: %(uid)s
sambaSID: %(sid)s
sambaNTPassword: %(ntpwd)s
sambaLMPassword: %(lmpwd)s
userPassword: %(pwd)s
"""

n = int(sys.argv.pop(1))

print container_template
for x in range(n):
    secret = 'secret%d' % x
    nt_secret = smbpasswd.nthash(secret)
    lm_secret = smbpasswd.lmhash(secret)
    print user_template % dict(
            uid='uid%d' % x,
            sid='12345',
            pwd=secret,
            ntpwd=nt_secret,
            lmpwd=lm_secret,
            ),
