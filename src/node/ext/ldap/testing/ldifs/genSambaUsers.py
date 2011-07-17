#!/usr/bin/env python

import sys
import smbpasswd

container_template = """\
dn: ou=sambaUsers,dc=my-domain,dc=com
objectClass: organizationalUnit
ou: %(ou)s
"""

user_template = """\
dn: uid=%(uid)s,ou=sambaUsers,dc=my-domain,dc=com
objectClass: account
objectClass: posixAccount
objectClass: shadowAccount
objectClass: sambaSamAccount
uid: %(uid)s
cn: %(cn)s
uidNumber: %(uid_num)s
gidNumber: %(uid_num)s
homeDirectory: %(home_dir)s
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
            cn='cn%d' % x,
            uid_num=str(x),
            gid_num=str(x),
            home_dir='/home/uid%d' % x,
            sid='12345-%d' % x,
            pwd=secret,
            ntpwd=nt_secret,
            lmpwd=lm_secret,
            ),
