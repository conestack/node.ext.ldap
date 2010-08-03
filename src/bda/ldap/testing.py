from bda.ldap import LDAPProps
from bda.ldap.groups import LDAPGroupsConfig
from bda.ldap.users import LDAPUsersConfig
from bda.ldap import SUBTREE

user = 'cn=Manager,dc=my-domain,dc=com'
pwd = 'secret'
props = LDAPProps('127.0.0.1', 12345, user, pwd, cache=False)
ucfg = LDAPUsersConfig(
        props,
        baseDN='dc=my-domain,dc=com',
        id_attr='sn',
        login_attr='description',
        scope=SUBTREE,
        queryFilter='(objectClass=person)',
        )
#gcfg_openldap = LDAPGroupsConfig(
#        props,
#        baseDN='dc=my-domain,dc=com',
#        id_attr='cn',
#        scope=SUBTREE,
#        queryFilter='(objectClass=groupOfNames)',
#        member_relation='member:dn',
#        )
