from node.ext.ldap import LDAPNode
from node.ext.ldap import testing
from node.ext.ldap.scope import SUBTREE
from node.ext.ldap.ugm import defaults
from node.ext.ldap.ugm import Groups
from node.ext.ldap.ugm import GroupsConfig
from node.ext.ldap.ugm import posix
from node.ext.ldap.ugm import samba
from node.ext.ldap.ugm import shadow
from node.ext.ldap.ugm import Users
from node.ext.ldap.ugm import UsersConfig
from node.tests import NodeTestCase
from odict import odict


layer = testing.LDIF_data


def defaults_container(fn):
    def wrapper(self):
        props = layer['props']
        root = LDAPNode('dc=my-domain,dc=com', props)
        container = root['ou=defaults'] = LDAPNode()
        container.attrs['objectClass'] = ['organizationalUnit']
        root()
        try:
            fn(self, props)
        finally:
            container.clear()
            container()
            del root['ou=defaults']
            root()
    return wrapper


class TestUGMDefaults(NodeTestCase):
    layer = layer

    def test_defaults(self):
        # Creation defaults
        self.assertEqual(defaults.creation_defaults, {
            'shadowAccount': {
                'uid': posix.uid
            },
            'posixGroup': {
                'gidNumber': posix.gidNumber,
                'cn': posix.cn
            },
            'sambaGroupMapping': {
                'sambaGroupType': samba.sambaGroupType,
                'gidNumber': posix.gidNumber,
                'sambaSID': samba.sambaGroupSID
            },
            'posixAccount': {
                'gidNumber': posix.gidNumber,
                'homeDirectory': posix.homeDirectory,
                'uidNumber': posix.uidNumber,
                'cn': posix.cn,
                'uid': posix.uid
            },
            'sambaSamAccount': {
                'sambaSID': samba.sambaUserSID
            }
        })

    @defaults_container
    def test_posix_account(self, props):
        ucfg = UsersConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((
                ('rdn', 'cn'),
                ('id', 'cn')
            )),
            scope=SUBTREE,
            queryFilter='(objectClass=posixAccount)',
            objectClasses=['account', 'posixAccount'],
            defaults={}
        )
        users = Users(props, ucfg)
        user = users.create('posixuser')
        user()
        self.assertEqual(sorted(user.context.attrs.items()), [
            (u'cn', u'posixuser'),
            (u'gidNumber', u'100'),
            (u'homeDirectory', u'/home/posixuser'),
            (u'objectClass', [u'account', u'posixAccount']),
            (u'uid', u'posixuser'),
            (u'uidNumber', u'100')
        ])

        defaults.creation_defaults['posixAccount']['loginShell'] = posix.loginShell
        ucfg = UsersConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((
                ('rdn', 'uid'),
                ('id', 'uid')
            )),
            scope=SUBTREE,
            queryFilter='(objectClass=posixAccount)',
            objectClasses=['account', 'posixAccount'],
            defaults={}
        )
        users = Users(props, ucfg)
        user = users.create('posixuser1')
        user()
        self.assertEqual(sorted(user.context.attrs.items()), [
            (u'cn', u'posixuser1'),
            (u'gidNumber', u'101'),
            (u'homeDirectory', u'/home/posixuser1'),
            (u'loginShell', u'/bin/false'),
            (u'objectClass', [u'account', u'posixAccount']),
            (u'uid', u'posixuser1'),
            (u'uidNumber', u'101')
        ])
        del defaults.creation_defaults['posixAccount']['loginShell']

    @defaults_container
    def test_posix_group(self, props):
        gcfg = GroupsConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((
                ('rdn', 'cn'),
                ('id', 'cn')
            )),
            scope=SUBTREE,
            queryFilter='(objectClass=posixGroup)',
            objectClasses=['posixGroup'],
            defaults={}
        )
        groups = Groups(props, gcfg)
        group = groups.create('posixgroup')
        group()
        self.assertEqual(sorted(group.context.attrs.items()), [
            (u'cn', u'posixgroup'),
            (u'gidNumber', u'100'),
            (u'memberUid', ['nobody']),
            (u'objectClass', [u'posixGroup'])
        ])

    @defaults_container
    def test_shadow_account(self, props):
        ucfg = UsersConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((
                ('rdn', 'uid'),
                ('id', 'uid')
            )),
            scope=SUBTREE,
            queryFilter='(objectClass=shadowAccount)',
            objectClasses=['account', 'shadowAccount'],
            defaults={}
        )
        users = Users(props, ucfg)
        user = users.create('shadowuser')
        user()
        self.assertEqual(sorted(user.context.attrs.items()), [
            (u'objectClass', [u'account', u'shadowAccount']),
            (u'uid', u'shadowuser')
        ])

        shadow_d = defaults.creation_defaults['shadowAccount']
        shadow_d['shadowFlag'] = shadow.shadowFlag
        shadow_d['shadowMin'] = shadow.shadowMin
        shadow_d['shadowMax'] = shadow.shadowMax
        shadow_d['shadowWarning'] = shadow.shadowWarning
        shadow_d['shadowInactive'] = shadow.shadowInactive
        shadow_d['shadowLastChange'] = shadow.shadowLastChange
        shadow_d['shadowExpire'] = shadow.shadowExpire

        ucfg = UsersConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((
                ('rdn', 'uid'),
                ('id', 'uid')
            )),
            scope=SUBTREE,
            queryFilter='(objectClass=shadowAccount)',
            objectClasses=['account', 'shadowAccount'],
            defaults={}
        )
        users = Users(props, ucfg)
        user = users.create('shadowuser2')
        user()
        self.assertEqual(sorted(user.context.attrs.items()), [
            (u'objectClass', [u'account', u'shadowAccount']),
            (u'shadowExpire', u'99999'),
            (u'shadowFlag', u'0'),
            (u'shadowInactive', u'0'),
            (u'shadowLastChange', u'12011'),
            (u'shadowMax', u'99999'),
            (u'shadowMin', u'0'),
            (u'shadowWarning', u'0'),
            (u'uid', u'shadowuser2')
        ])

        del shadow_d['shadowFlag']
        del shadow_d['shadowMin']
        del shadow_d['shadowMax']
        del shadow_d['shadowWarning']
        del shadow_d['shadowInactive']
        del shadow_d['shadowLastChange']
        del shadow_d['shadowExpire']

    @defaults_container
    def test_samba_account(self, props):
        ucfg = UsersConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((
                ('rdn', 'cn'),
                ('id', 'cn')
            )),
            scope=SUBTREE,
            queryFilter='(objectClass=sambaSamAccount)',
            objectClasses=['account', 'posixAccount', 'sambaSamAccount'],
            defaults={
                'uid': 'sambauser',
            }
        )
        users = Users(props, ucfg)
        user = users.create('sambauser')
        user()
        self.assertEqual(sorted(user.context.attrs.items()), [
            (u'cn', u'sambauser'),
            (u'gidNumber', u'100'),
            (u'homeDirectory', u'/home/sambauser'),
            (u'objectClass', [u'account', u'posixAccount', u'sambaSamAccount']),
            (u'sambaSID', u'S-1-5-21-1234567890-1234567890-1234567890-1202'),
            (u'uid', u'sambauser'),
            (u'uidNumber', u'100')
        ])

        user.passwd(None, 'secret')
        res = sorted(user.context.attrs.items())
        self.assertEqual(res[:-1], [
            (u'cn', u'sambauser'),
            (u'gidNumber', u'100'),
            (u'homeDirectory', u'/home/sambauser'),
            (u'objectClass', [u'account', u'posixAccount', u'sambaSamAccount']),
            (u'sambaLMPassword', u'552902031bede9efaad3b435b51404ee'),
            (u'sambaNTPassword', u'878d8014606cda29677a44efa1353fc7'),
            (u'sambaSID', u'S-1-5-21-1234567890-1234567890-1234567890-1202'),
            (u'uid', u'sambauser'),
            (u'uidNumber', u'100')
        ])
        self.assertEqual(res[-1][0], 'userPassword')
        self.assertTrue(res[-1][1].startswith('{SSHA}'))

        samba_d = defaults.creation_defaults['sambaSamAccount']
        samba_d['sambaDomainName'] = samba.sambaDomainName
        samba_d['sambaPrimaryGroupSID'] = samba.sambaPrimaryGroupSID
        samba_d['sambaAcctFlags'] = samba.sambaAcctFlags

        ucfg = UsersConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((
                ('rdn', 'cn'),
                ('id', 'cn')
            )),
            scope=SUBTREE,
            queryFilter='(objectClass=sambaSamAccount)',
            objectClasses=['account', 'posixAccount', 'sambaSamAccount'],
            defaults={
                'uid': 'sambauser1',
            }
        )
        users = Users(props, ucfg)
        user = users.create('sambauser1')
        user()
        self.assertEqual(sorted(user.context.attrs.items()), [
            (u'cn', u'sambauser1'),
            (u'gidNumber', u'101'),
            (u'homeDirectory', u'/home/sambauser1'),
            (u'objectClass', [u'account', u'posixAccount', u'sambaSamAccount']),
            (u'sambaAcctFlags', u'[U]'),
            (u'sambaDomainName', u'CONE_UGM'),
            (u'sambaPrimaryGroupSID', u'S-1-5-21-1234567890-1234567890-1234567890-123'),
            (u'sambaSID', u'S-1-5-21-1234567890-1234567890-1234567890-1202'),
            (u'uid', u'sambauser1'),
            (u'uidNumber', u'101')
        ])

        del samba_d['sambaDomainName']
        del samba_d['sambaPrimaryGroupSID']
        del samba_d['sambaAcctFlags']

    @defaults_container
    def test_samba_group(self, props):
        gcfg = GroupsConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((
                ('rdn', 'cn'),
                ('id', 'cn')
            )),
            scope=SUBTREE,
            queryFilter='(objectClass=sambaGroupMapping)',
            objectClasses=['posixGroup', 'sambaGroupMapping'],
            defaults={}
        )
        groups = Groups(props, gcfg)
        group = groups.create('sambagroup')
        group()
        self.assertEqual(sorted(group.context.attrs.items()), [
            (u'cn', u'sambagroup'),
            (u'gidNumber', u'100'),
            (u'memberUid', ['nobody']),
            (u'objectClass', [u'posixGroup', u'sambaGroupMapping']),
            (u'sambaGroupType', u'2'),
            (u'sambaSID', u'S-1-5-21-1234567890-1234567890-1234567890-1202')
        ])
