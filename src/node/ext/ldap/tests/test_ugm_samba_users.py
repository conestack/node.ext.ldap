from node.ext.ldap import testing
from node.ext.ldap.ugm import Ugm
from node.tests import NodeTestCase


class TestUGMSambaUsers(NodeTestCase):
    layer = testing.LDIF_sambaUsers

    def test_samba_users(self):
        ucfg = self.layer['ucfg']
        gcfg = self.layer['gcfg']
        props = self.layer['props']

        ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg)
        self.assertEqual(ugm.users.search(), ['uid0', 'uid1', 'uid2'])
        self.assertEqual(ugm.users['uid0'].context.attrs['userPassword'], 'secret0')
        self.assertEqual(
            ugm.users['uid0'].context.attrs['sambaLMPassword'],
            'FF3750BCC2B22412AAD3B435B51404EE',
        )
        self.assertEqual(
            ugm.users['uid0'].context.attrs['sambaNTPassword'],
            '62CF067F093CD75BBAA5D49E04689ED7',
        )
        ugm.users['uid0'].passwd('secret0', 'newsecret')
        password = ugm.users['uid0'].context.attrs['userPassword']
        self.assertTrue(password.startswith('{SSHA}'))
        self.assertEqual(
            ugm.users['uid0'].context.attrs['sambaLMPassword'],
            'db6574a2642d294b9a0f5d12d8f612d0',
        )
        self.assertEqual(
            ugm.users['uid0'].context.attrs['sambaNTPassword'],
            '58d9f1588236ee9d4ed739e89ffca25b',
        )
