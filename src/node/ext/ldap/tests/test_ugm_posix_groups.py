from node.ext.ldap import LDAPNode
from node.ext.ldap import SUBTREE
from node.ext.ldap import testing
from node.ext.ldap.ugm import Group
from node.ext.ldap.ugm import Groups
from node.ext.ldap.ugm import RolesConfig
from node.ext.ldap.ugm import Ugm
from node.ext.ldap.ugm import User
from node.ext.ldap.ugm import Users
from node.ext.ldap.ugm._api import ACCOUNT_EXPIRED
from node.ext.ldap.ugm._api import PrincipalAliasedAttributes
from node.tests import NodeTestCase
from odict import odict
import ldap


layer = testing.LDIF_posixGroups


def create_ugm():
    props = layer['props']
    ucfg = layer['ucfg']
    gcfg = layer['gcfg']
    rcfg = None  # XXX: later
    return Ugm(name='ugm', parent=None, props=props, ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)


def posix_groups_ugm(fn):
    def wrapper(self):
        fn(self, create_ugm())
    return wrapper


class TestUGMPosixGroups(NodeTestCase):
    layer = layer

    @posix_groups_ugm
    def test_basics(self, ugm):
        # Users object
        self.assertTrue(isinstance(ugm.users, Users))
        self.assertTrue(ugm['users'] is ugm.users)

        # Groups object
        self.assertTrue(isinstance(ugm.groups, Groups))
        self.assertTrue(ugm['groups'] is ugm.groups)

        # Try to delete from UGM, fails
        err = self.expect_error(
            NotImplementedError,
            ugm.__delitem__,
            'users'
        )
        self.assertEqual(str(err), 'Operation forbidden on this node.')

        # Try to set item by invalid key, fails
        err = self.expect_error(
            KeyError,
            ugm.__setitem__,
            'inexistent',
            ugm.users
        )
        self.assertEqual(str(err), "'inexistent'")

    @posix_groups_ugm
    def test_fetch_users(self, ugm):
        # User keys
        users = ugm.users
        self.assertEqual(users.keys(), [u'uid0', u'uid1', u'uid2'])

        # Fetch some users
        user_0 = users['uid0']
        user_1 = users['uid1']
        user_2 = users['uid2']

        self.assertEqual(users.values(), [user_0, user_1, user_2])
        self.assertTrue(isinstance(user_0, User))
        self.assertTrue(isinstance(user_0.attrs, PrincipalAliasedAttributes))
        self.assertEqual(user_0.attrs['cn'], 'cn0')
        self.assertEqual(user_0.attrs['sn'], 'sn0')
        self.assertEqual(user_0.attrs['login'], 'cn0')

        # XXX: LDAPNodeAttributes.items does not return consistent results if
        #      attrmap points to same attribute multiple times
        self.assertEqual(sorted(user_0.attrs.items()), [
            ('gidNumber', u'0'),
            ('homeDirectory', u'/home/uid0'),
            ('login', u'cn0'),
            ('rdn', u'uid0'),
            ('sn', u'sn0'),
            ('uidNumber', u'0')
        ])

        # User is a leaf
        err = self.expect_error(
            NotImplementedError,
            user_0.__setitem__,
            'foo',
            object()
        )
        self.assertEqual(str(err), 'User does not support ``__setitem__``')
        err = self.expect_error(
            NotImplementedError,
            user_0.__delitem__,
            'foo'
        )
        self.assertEqual(str(err), 'User does not support ``__delitem__``')
        err = self.expect_error(
            NotImplementedError,
            user_0.__getitem__,
            'foo'
        )
        self.assertEqual(str(err), 'User does not support ``__getitem__``')
        self.assertEqual(user_0.keys(), [])

    @posix_groups_ugm
    def test_authenticate(self, ugm):
        # Authenticate
        self.assertEqual(ugm.users.authenticate('uid0', 'secret0'), 'uid0')
        self.assertEqual(ugm.users.authenticate('cn0', 'secret0'), 'uid0')
        self.assertEqual(ugm.users.authenticate('uid0', 'invalid'), False)
        self.assertEqual(ugm.users.authenticate('cn0', 'invalid'), False)
        self.assertEqual(ugm.users.authenticate('foo', 'secret0'), False)

    @posix_groups_ugm
    def test_account_expiration(self, ugm):
        users = ugm.users

        # Note: after changind expires attribute, user must be pesisted in
        # order to take expiration effect for authentication. Expires attribute
        # lookup is done against LDAP directly in ``users.authenticate``

        # Expires attribute not set yet
        self.assertEqual(users.expiresAttr, None)
        self.assertFalse(users['uid0'].expired)

        # Set expires attribute for ongoing tests
        users.expiresAttr = 'shadowExpire'

        # Value 99999 and -1 means no expiration
        self.assertEqual(users['uid0'].context.attrs['shadowExpire'], u'99999')
        self.assertEqual(users['uid0'].context.attrs['shadowInactive'], u'0')
        self.assertEqual(users.authenticate('uid0', 'secret0'), u'uid0')
        self.assertFalse(users['uid0'].expired)

        # Expire a while ago
        users['uid0'].context.attrs['shadowExpire'] = '1'
        users['uid0']()

        res = users.authenticate('uid0', 'secret0')
        self.assertEqual(res, ACCOUNT_EXPIRED)
        self.assertFalse(bool(res))
        self.assertTrue(users['uid0'].expired)

        # No expiration far future
        users['uid0'].context.attrs['shadowExpire'] = '99999'
        users['uid0']()
        self.assertEqual(users.authenticate('uid0', 'secret0'), u'uid0')
        self.assertFalse(users['uid0'].expired)

        # No expiration by '-1'
        users['uid0'].context.attrs['shadowExpire'] = '-1'
        users['uid0']()
        self.assertEqual(users.authenticate('uid0', 'secret0'), u'uid0')
        self.assertFalse(users['uid0'].expired)

        # Invalid expiration field data
        users.expiresAttr = 'uid'
        self.assertFalse(users.authenticate('uid0', 'secret0'))

        # XXX: figure out shadowInactive -> PAM and samba seem to ignore -> configuration?
        # users['uid0'].context.attrs['shadowInactive'] = u'99999'

        # Uid0 never expires - or at leas expires in many years and even if, there are
        # 99999 more days unless account gets disabled

        # self.assertEqual(users.authenticate('uid0', 'secret0'), u'uid0')
        # users['uid0'].context.attrs['shadowInactive'] = '0'

    @posix_groups_ugm
    def test_change_password(self, ugm):
        err = self.expect_error(
            ldap.UNWILLING_TO_PERFORM,
            ugm.users.passwd,
            'uid0',
            'foo',
            'bar'
        )
        self.assertEqual(err.args[0], {
            'msgtype': 120,
            'msgid': 4,
            'result': 53,
            'desc': 'Server is unwilling to perform',
            'ctrls': [],
            'info': 'unwilling to verify old password'
        })

        self.expect_error(
            KeyError,
            ugm.users.passwd,
            'foo',
            'secret0',
            'bar'
        )

        ugm.users.passwd('uid0', 'secret0', 'bar')
        self.assertEqual(ugm.users.authenticate('uid0', 'bar'), 'uid0')

        ugm.users.expiresAttr = 'shadowExpire'
        ugm.users.passwd('uid0', 'bar', 'secret0')
        self.assertEqual(ugm.users.authenticate('uid0', 'secret0'), 'uid0')

    @posix_groups_ugm
    def test_add_user(self, ugm):
        users = ugm.users
        self.check_output("""
        <class 'node.ext.ldap.ugm._api.Users'>: users
          <class 'node.ext.ldap.ugm._api.User'>: uid0
          <class 'node.ext.ldap.ugm._api.User'>: uid1
          <class 'node.ext.ldap.ugm._api.User'>: uid2
        """, users.treerepr())

        user = users.create(
            'sepp',
            cn='Sepp',
            sn='Unterwurzacher',
            uidNumber='99',
            gidNumber='99',
            homeDirectory='home/sepp'
        )
        self.assertTrue(isinstance(user, User))

        # The user is added to tree
        self.check_output("""
        <class 'node.ext.ldap.ugm._api.Users'>: users
          <class 'node.ext.ldap.ugm._api.User'>: uid0
          <class 'node.ext.ldap.ugm._api.User'>: uid1
          <class 'node.ext.ldap.ugm._api.User'>: uid2
          <class 'node.ext.ldap.ugm._api.User'>: sepp
        """, users.treerepr())

        # Though, no authentication or password setting possible yet, because
        # tree is not persisted to LDAP yet
        self.assertFalse(users.authenticate('sepp', 'secret'))
        self.expect_error(
            KeyError,
            ugm.users.passwd,
            'sepp',
            None,
            'secret'
        )

        # After calling, new user is available in LDAP
        ugm()
        ugm.users.passwd('sepp', None, 'secret')
        self.assertEqual(users.authenticate('sepp', 'secret'), 'sepp')

        # Delete already created user
        del users['sepp']
        ugm()

    @posix_groups_ugm
    def test_fetch_groups(self, ugm):
        groups = ugm.groups
        self.assertEqual(groups.keys(), [u'group0', u'group1', u'group2'])

        group_0 = groups['group0']
        group_1 = groups['group1']
        group_2 = groups['group2']

        self.assertEqual(groups.values(), [group_0, group_1, group_2])
        self.assertTrue(isinstance(group_0, Group))
        self.assertTrue(isinstance(group_0.attrs, PrincipalAliasedAttributes))
        self.assertEqual(sorted(group_0.attrs.items()), [
            ('gidNumber', '0'),
            ('memberUid', ['nobody', 'uid0']),
            ('rdn', 'group0')
        ])
        self.assertEqual(sorted(group_1.attrs.items()), [
            ('gidNumber', u'1'),
            ('memberUid', [u'nobody', u'uid0', u'uid1']),
            ('rdn', u'group1')
        ])

    @posix_groups_ugm
    def test_add_group(self, ugm):
        groups = ugm.groups
        group = groups.create('group99', id='group99')
        self.assertTrue(isinstance(group, Group))

        ugm()
        self.check_output("""
        <class 'node.ext.ldap.ugm._api.Groups'>: groups
          <class 'node.ext.ldap.ugm._api.Group'>: group0
            <class 'node.ext.ldap.ugm._api.User'>: uid0
          <class 'node.ext.ldap.ugm._api.Group'>: group1
            <class 'node.ext.ldap.ugm._api.User'>: uid0
            <class 'node.ext.ldap.ugm._api.User'>: uid1
          <class 'node.ext.ldap.ugm._api.Group'>: group2
            <class 'node.ext.ldap.ugm._api.User'>: uid0
            <class 'node.ext.ldap.ugm._api.User'>: uid1
            <class 'node.ext.ldap.ugm._api.User'>: uid2
          <class 'node.ext.ldap.ugm._api.Group'>: group99
        """, groups.treerepr())

        # Delete already created group
        del groups['group99']
        ugm()
        self.check_output("""
        <class 'node.ext.ldap.ugm._api.Groups'>: groups
          <class 'node.ext.ldap.ugm._api.Group'>: group0
            <class 'node.ext.ldap.ugm._api.User'>: uid0
          <class 'node.ext.ldap.ugm._api.Group'>: group1
            <class 'node.ext.ldap.ugm._api.User'>: uid0
            <class 'node.ext.ldap.ugm._api.User'>: uid1
          <class 'node.ext.ldap.ugm._api.Group'>: group2
            <class 'node.ext.ldap.ugm._api.User'>: uid0
            <class 'node.ext.ldap.ugm._api.User'>: uid1
            <class 'node.ext.ldap.ugm._api.User'>: uid2
        """, groups.treerepr())

    @posix_groups_ugm
    def test_group_memebership(self, ugm):
        users = ugm.users
        groups = ugm.groups

        # A group returns the members ids as keys
        group_0 = groups['group0']
        group_1 = groups['group1']
        group_2 = groups['group2']

        self.assertEqual(group_0.member_ids, ['uid0'])
        self.assertEqual(group_1.member_ids, ['uid0', 'uid1'])
        self.assertEqual(group_2.member_ids, ['uid0', 'uid1', 'uid2'])

        # The member users are fetched via ``__getitem__``
        user_1 = ugm.users['uid1']
        self.assertTrue(user_1 is group_1['uid1'])

        # Querying a group for a non-member results in a KeyError
        self.expect_error(KeyError, group_0.__getitem__, 'uid1')

        # Deleting inexistend member from group fails
        self.expect_error(KeyError, group_0.__delitem__, 'inexistent')

        # ``__setitem__`` is prohibited
        err = self.expect_error(
            NotImplementedError,
            group_1.__setitem__,
            'uid0',
            users['uid0']
        )
        self.assertEqual(str(err), 'Group does not support ``__setitem__``')

        # Members are added via ``add``
        group_0.add('uid1')
        self.assertEqual(group_0.keys(), [u'uid0', u'uid1'])
        self.assertEqual(group_0.member_ids, [u'uid0', u'uid1'])
        self.assertTrue(group_0['uid0'] is ugm.users['uid0'])
        self.assertEqual(group_0.users, [users['uid0'], users['uid1']])

        group_0()

        # Let's take a fresh view on ldap whether this really happened
        ugm_fresh = create_ugm()
        self.assertEqual(ugm_fresh.groups['group0'].keys(), [u'uid0', u'uid1'])

        # Members are removed via ``delitem``
        del group_0['uid1']
        ugm_fresh = create_ugm()
        self.assertEqual(ugm_fresh.groups['group0'].keys(), [u'uid0'])

        user_0 = ugm_fresh.users['uid0']
        user_1 = ugm_fresh.users['uid1']
        user_2 = ugm_fresh.users['uid2']

        # A user knows its groups
        self.assertEqual(user_0.groups, [
            ugm_fresh.groups['group0'],
            ugm_fresh.groups['group1'],
            ugm_fresh.groups['group2']
        ])
        self.assertEqual(user_1.groups, [
            ugm_fresh.groups['group1'],
            ugm_fresh.groups['group2']
        ])
        self.assertEqual(user_2.groups, [
            ugm_fresh.groups['group2']
        ])
        self.assertEqual(user_0.group_ids, ['group0', 'group1', 'group2'])
        self.assertEqual(user_1.group_ids, ['group1', 'group2'])
        self.assertEqual(user_2.group_ids, ['group2'])

    @posix_groups_ugm
    def test_search(self, ugm):
        users = ugm.users
        groups = ugm.groups

        # Test search function
        self.assertEqual(users.search(criteria={'login': 'cn0'}), [u'uid0'])
        self.assertEqual(groups.search(criteria={'id': 'group2'}), [u'group2'])

    @posix_groups_ugm
    def test_ids(self, ugm):
        users = ugm.users
        groups = ugm.groups

        # There's an ids property on principals base class
        self.assertEqual(users.ids, [u'uid0', u'uid1', u'uid2'])
        self.assertEqual(groups.ids, [u'group0', u'group1', u'group2'])

    @posix_groups_ugm
    def test_membership_assignment(self, ugm):
        users = ugm.users
        groups = ugm.groups

        # Add user to some groups and then delete user, check whether user
        # is removed from all this groups.
        user = users.create(
            'sepp',
            cn='Sepp',
            sn='Unterwurzacher',
            uidNumber='99',
            gidNumber='99',
            homeDirectory='home/sepp'
        )
        groups['group0'].add('sepp')
        groups['group1'].add('sepp')
        ugm()

        self.assertEqual(user.groups, [groups['group0'], groups['group1']])
        self.assertEqual(user.group_ids, [u'group0', u'group1'])
        self.check_output("""
        <class 'node.ext.ldap.ugm._api.Ugm'>: ugm
          <class 'node.ext.ldap.ugm._api.Users'>: users
            <class 'node.ext.ldap.ugm._api.User'>: uid0
            <class 'node.ext.ldap.ugm._api.User'>: uid1
            <class 'node.ext.ldap.ugm._api.User'>: uid2
            <class 'node.ext.ldap.ugm._api.User'>: sepp
          <class 'node.ext.ldap.ugm._api.Groups'>: groups
            <class 'node.ext.ldap.ugm._api.Group'>: group0
              <class 'node.ext.ldap.ugm._api.User'>: sepp
              <class 'node.ext.ldap.ugm._api.User'>: uid0
            <class 'node.ext.ldap.ugm._api.Group'>: group1
              <class 'node.ext.ldap.ugm._api.User'>: sepp
              <class 'node.ext.ldap.ugm._api.User'>: uid0
              <class 'node.ext.ldap.ugm._api.User'>: uid1
            <class 'node.ext.ldap.ugm._api.Group'>: group2
              <class 'node.ext.ldap.ugm._api.User'>: uid0
              <class 'node.ext.ldap.ugm._api.User'>: uid1
              <class 'node.ext.ldap.ugm._api.User'>: uid2
        """, ugm.treerepr())

        del users['sepp']
        ugm()
        self.check_output("""
        <class 'node.ext.ldap.ugm._api.Ugm'>: ugm
          <class 'node.ext.ldap.ugm._api.Users'>: users
            <class 'node.ext.ldap.ugm._api.User'>: uid0
            <class 'node.ext.ldap.ugm._api.User'>: uid1
            <class 'node.ext.ldap.ugm._api.User'>: uid2
          <class 'node.ext.ldap.ugm._api.Groups'>: groups
            <class 'node.ext.ldap.ugm._api.Group'>: group0
              <class 'node.ext.ldap.ugm._api.User'>: uid0
            <class 'node.ext.ldap.ugm._api.Group'>: group1
              <class 'node.ext.ldap.ugm._api.User'>: uid0
              <class 'node.ext.ldap.ugm._api.User'>: uid1
            <class 'node.ext.ldap.ugm._api.Group'>: group2
              <class 'node.ext.ldap.ugm._api.User'>: uid0
              <class 'node.ext.ldap.ugm._api.User'>: uid1
              <class 'node.ext.ldap.ugm._api.User'>: uid2
        """, ugm.treerepr())

    @posix_groups_ugm
    def test_no_member_uid_attribute_yet(self, ugm):
        # Test case where group object does not have 'memberUid' attribute
        # set yet.
        node = LDAPNode(
            u'cn=group0,ou=groups,ou=posixGroups,dc=my-domain,dc=com',
            props=self.layer['props']
        )
        del node.attrs['memberUid']
        node()

        group = ugm.groups['group0']
        self.assertEqual(group.items(), [])

        group.add('uid0')
        group()

        node = LDAPNode(
            u'cn=group0,ou=groups,ou=posixGroups,dc=my-domain,dc=com',
            props=self.layer['props']
        )
        self.assertEqual(node.attrs['memberUid'], ['uid0'])

    @posix_groups_ugm
    def test_inexistent_member_reference(self, ugm):
        # Test case where group contains reference to inexistent member.
        node = LDAPNode(
            u'cn=group0,ou=groups,ou=posixGroups,dc=my-domain,dc=com',
            props=self.layer['props']
        )
        node.attrs['memberUid'] = ['uid0', 'inexistent']
        node()

        group = ugm.groups['group0']
        self.assertEqual(group.keys(), ['uid0'])

        node.attrs['memberUid'] = ['uid0']
        node()

    def test_roles(self):
        # Role Management. Create container for roles.
        props = layer['props']
        node = LDAPNode('dc=my-domain,dc=com', props)
        node['ou=roles'] = LDAPNode()
        node['ou=roles'].attrs['objectClass'] = ['organizationalUnit']
        node()

        ucfg = layer['ucfg']
        gcfg = layer['gcfg']
        rcfg = RolesConfig(
            baseDN='ou=roles,dc=my-domain,dc=com',
            attrmap=odict((
                ('rdn', 'cn'),
                ('id', 'cn')
            )),
            scope=SUBTREE,
            queryFilter='(objectClass=posixGroup)',
            objectClasses=['posixGroup'],
            defaults={},
            strict=False
        )
        ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)

        user = ugm.users['uid1']
        self.assertEqual(ugm.roles(user), [])

        ugm.add_role('viewer', user)
        self.assertEqual(ugm.roles(user), ['viewer'])
        self.assertEqual(user.roles, ['viewer'])

        user = ugm.users['uid2']
        user.add_role('viewer')
        user.add_role('editor')
        self.assertEqual(sorted(user.roles), ['editor', 'viewer'])

        ugm.roles_storage()
        ugm.remove_role('viewer', user)
        user.remove_role('editor')
        self.assertEqual(user.roles, [])

        ugm.roles_storage()
        group = ugm.groups['group1']
        self.assertEqual(ugm.roles(group), [])

        ugm.add_role('viewer', group)
        self.assertEqual(ugm.roles(group), ['viewer'])
        self.assertEqual(group.roles, ['viewer'])

        group = ugm.groups['group0']
        group.add_role('viewer')
        group.add_role('editor')
        self.assertEqual(group.roles, ['viewer', 'editor'])

        ugm.roles_storage()
        err = self.expect_error(
            ValueError,
            group.add_role,
            'editor'
        )
        self.assertEqual(str(err), "Principal already has role 'editor'")

        ugm.remove_role('viewer', group)
        self.assertEqual(ugm.roles_storage.keys(), [u'viewer', u'editor'])

        group.remove_role('editor')
        self.assertEqual(ugm.roles_storage.keys(), [u'viewer'])
        self.assertEqual(ugm.roles_storage.storage.keys(), ['viewer'])

        self.expect_error(KeyError, ugm.roles_storage.__getitem__, 'editor')
        err = self.expect_error(
            ValueError,
            group.remove_role,
            'editor'
        )
        self.assertEqual(str(err), "Role not exists 'editor'")

        err = self.expect_error(
            ValueError,
            group.remove_role,
            'viewer'
        )
        self.assertEqual(str(err), "Principal does not has role 'viewer'")

        ugm.roles_storage()

        node = LDAPNode('dc=my-domain,dc=com', props)
        node['ou=roles'].clear()
        node['ou=roles']()
        del node['ou=roles']
        node()
