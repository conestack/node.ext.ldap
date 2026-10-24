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
from unittest import mock


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
        self.assertEqual(
            defaults.creation_defaults['posixAccount'],
            {
                'gidNumber': posix.gidNumber,
                'homeDirectory': posix.homeDirectory,
                'uidNumber': posix.uidNumber,
                'cn': posix.cn,
                'uid': posix.uid,
            },
        )
        self.assertEqual(
            defaults.creation_defaults['posixGroup'],
            {'gidNumber': posix.gidNumber, 'cn': posix.cn},
        )
        self.assertEqual(
            defaults.creation_defaults['sambaGroupMapping'],
            {
                'sambaGroupType': samba.sambaGroupType,
                'gidNumber': posix.gidNumber,
                'sambaSID': samba.sambaGroupSID,
            },
        )
        self.assertEqual(
            defaults.creation_defaults['sambaSamAccount'],
            {'sambaSID': samba.sambaUserSID},
        )
        self.assertEqual(defaults.creation_defaults['shadowAccount'], {'uid': posix.uid})

    @defaults_container
    def test_posix_account(self, props):
        ucfg = UsersConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((('rdn', 'cn'), ('id', 'cn'))),
            scope=SUBTREE,
            queryFilter='(objectClass=posixAccount)',
            objectClasses=['account', 'posixAccount'],
            defaults={},
        )
        users = Users(props, ucfg)
        user = users.create('posixuser')
        user()
        self.assertEqual(
            sorted(user.context.attrs.items()),
            [
                ('cn', 'posixuser'),
                ('gidNumber', '100'),
                ('homeDirectory', '/home/posixuser'),
                ('objectClass', ['account', 'posixAccount']),
                ('uid', 'posixuser'),
                ('uidNumber', '100'),
            ],
        )

        defaults.creation_defaults['posixAccount']['loginShell'] = posix.loginShell
        ucfg = UsersConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((('rdn', 'uid'), ('id', 'uid'))),
            scope=SUBTREE,
            queryFilter='(objectClass=posixAccount)',
            objectClasses=['account', 'posixAccount'],
            defaults={},
        )
        users = Users(props, ucfg)
        user = users.create('posixuser1')
        user()
        self.assertEqual(
            sorted(user.context.attrs.items()),
            [
                ('cn', 'posixuser1'),
                ('gidNumber', '101'),
                ('homeDirectory', '/home/posixuser1'),
                ('loginShell', '/bin/false'),
                ('objectClass', ['account', 'posixAccount']),
                ('uid', 'posixuser1'),
                ('uidNumber', '101'),
            ],
        )
        del defaults.creation_defaults['posixAccount']['loginShell']

    @defaults_container
    def test_posix_group(self, props):
        gcfg = GroupsConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((('rdn', 'cn'), ('id', 'cn'))),
            scope=SUBTREE,
            queryFilter='(objectClass=posixGroup)',
            objectClasses=['posixGroup'],
            defaults={},
        )
        groups = Groups(props, gcfg)
        group = groups.create('posixgroup')
        group()
        self.assertEqual(
            sorted(group.context.attrs.items()),
            [
                ('cn', 'posixgroup'),
                ('gidNumber', '100'),
                ('memberUid', ['nobody']),
                ('objectClass', ['posixGroup']),
            ],
        )

    def test_posix_member_uid(self):
        self.assertEqual(posix.memberUid(None, 'cn=posixgroup'), ['nobody'])

    @defaults_container
    def test_shadow_account(self, props):
        ucfg = UsersConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((('rdn', 'uid'), ('id', 'uid'))),
            scope=SUBTREE,
            queryFilter='(objectClass=shadowAccount)',
            objectClasses=['account', 'shadowAccount'],
            defaults={},
        )
        users = Users(props, ucfg)
        user = users.create('shadowuser')
        user()
        self.assertEqual(
            sorted(user.context.attrs.items()),
            [('objectClass', ['account', 'shadowAccount']), ('uid', 'shadowuser')],
        )

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
            attrmap=odict((('rdn', 'uid'), ('id', 'uid'))),
            scope=SUBTREE,
            queryFilter='(objectClass=shadowAccount)',
            objectClasses=['account', 'shadowAccount'],
            defaults={},
        )
        users = Users(props, ucfg)
        user = users.create('shadowuser2')
        user()
        self.assertEqual(
            sorted(user.context.attrs.items()),
            [
                ('objectClass', ['account', 'shadowAccount']),
                ('shadowExpire', '99999'),
                ('shadowFlag', '0'),
                ('shadowInactive', '0'),
                ('shadowLastChange', '12011'),
                ('shadowMax', '99999'),
                ('shadowMin', '0'),
                ('shadowWarning', '0'),
                ('uid', 'shadowuser2'),
            ],
        )

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
            attrmap=odict((('rdn', 'cn'), ('id', 'cn'))),
            scope=SUBTREE,
            queryFilter='(objectClass=sambaSamAccount)',
            objectClasses=['account', 'posixAccount', 'sambaSamAccount'],
            defaults={
                'uid': 'sambauser',
            },
        )
        users = Users(props, ucfg)
        user = users.create('sambauser')
        user()
        self.assertEqual(
            sorted(user.context.attrs.items()),
            [
                ('cn', 'sambauser'),
                ('gidNumber', '100'),
                ('homeDirectory', '/home/sambauser'),
                ('objectClass', ['account', 'posixAccount', 'sambaSamAccount']),
                ('sambaSID', 'S-1-5-21-1234567890-1234567890-1234567890-1202'),
                ('uid', 'sambauser'),
                ('uidNumber', '100'),
            ],
        )

        user.passwd(None, 'secret')
        res = sorted(user.context.attrs.items())
        self.assertEqual(
            res[:-1],
            [
                ('cn', 'sambauser'),
                ('gidNumber', '100'),
                ('homeDirectory', '/home/sambauser'),
                ('objectClass', ['account', 'posixAccount', 'sambaSamAccount']),
                ('sambaLMPassword', '552902031bede9efaad3b435b51404ee'),
                ('sambaNTPassword', '878d8014606cda29677a44efa1353fc7'),
                ('sambaSID', 'S-1-5-21-1234567890-1234567890-1234567890-1202'),
                ('uid', 'sambauser'),
                ('uidNumber', '100'),
            ],
        )
        self.assertEqual(res[-1][0], 'userPassword')
        self.assertTrue(res[-1][1].startswith('{SSHA}'))

        samba_d = defaults.creation_defaults['sambaSamAccount']
        samba_d['sambaDomainName'] = samba.sambaDomainName
        samba_d['sambaPrimaryGroupSID'] = samba.sambaPrimaryGroupSID
        samba_d['sambaAcctFlags'] = samba.sambaAcctFlags

        ucfg = UsersConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((('rdn', 'cn'), ('id', 'cn'))),
            scope=SUBTREE,
            queryFilter='(objectClass=sambaSamAccount)',
            objectClasses=['account', 'posixAccount', 'sambaSamAccount'],
            defaults={
                'uid': 'sambauser1',
            },
        )
        users = Users(props, ucfg)
        user = users.create('sambauser1')
        user()
        self.assertEqual(
            sorted(user.context.attrs.items()),
            [
                ('cn', 'sambauser1'),
                ('gidNumber', '101'),
                ('homeDirectory', '/home/sambauser1'),
                ('objectClass', ['account', 'posixAccount', 'sambaSamAccount']),
                ('sambaAcctFlags', '[U]'),
                ('sambaDomainName', 'CONE_UGM'),
                ('sambaPrimaryGroupSID', 'S-1-5-21-1234567890-1234567890-1234567890-123'),
                ('sambaSID', 'S-1-5-21-1234567890-1234567890-1234567890-1202'),
                ('uid', 'sambauser1'),
                ('uidNumber', '101'),
            ],
        )

        del samba_d['sambaDomainName']
        del samba_d['sambaPrimaryGroupSID']
        del samba_d['sambaAcctFlags']

    def test_samba_pwd_last_set(self):
        with mock.patch('node.ext.ldap.ugm.samba.time') as time:
            time.time.return_value = 1234567890.5
            self.assertEqual(samba.sambaPwdLastSet(None, 'uid=sambauser'), '1234567890')

    @defaults_container
    def test_samba_group(self, props):
        gcfg = GroupsConfig(
            baseDN='ou=defaults,dc=my-domain,dc=com',
            attrmap=odict((('rdn', 'cn'), ('id', 'cn'))),
            scope=SUBTREE,
            queryFilter='(objectClass=sambaGroupMapping)',
            objectClasses=['posixGroup', 'sambaGroupMapping'],
            defaults={},
        )
        groups = Groups(props, gcfg)
        group = groups.create('sambagroup')
        group()
        self.assertEqual(
            sorted(group.context.attrs.items()),
            [
                ('cn', 'sambagroup'),
                ('gidNumber', '100'),
                ('memberUid', ['nobody']),
                ('objectClass', ['posixGroup', 'sambaGroupMapping']),
                ('sambaGroupType', '2'),
                ('sambaSID', 'S-1-5-21-1234567890-1234567890-1234567890-1202'),
            ],
        )
