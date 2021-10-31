from node.ext.ldap import testing
from node.ext.ldap.ugm import Group
from node.ext.ldap.ugm import Groups
from node.ext.ldap.ugm import Ugm
from node.ext.ldap.ugm import User
from node.ext.ldap.ugm import Users
from node.ext.ldap.ugm._api import PrincipalAliasedAttributes
from node.tests import NodeTestCase
import ldap


layer = testing.LDIF_groupOfNames


def create_ugm():
    props = layer['props']
    ucfg = layer['ucfg']
    gcfg = layer['gcfg']
    rcfg = None  # XXX: later
    return Ugm(name='ugm', parent=None, props=props, ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)


def group_of_names_ugm(fn):
    def wrapper(self):
        fn(self, create_ugm())
    return wrapper


class TestUGMGroupOfNames(NodeTestCase):
    layer = layer

    @group_of_names_ugm
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

        # Invalidate
        self.assertEqual(ugm.storage.keys(), ['users', 'groups'])
        ugm.invalidate(key='users')
        self.assertEqual(ugm.storage.keys(), ['groups'])
        ugm.invalidate()
        self.assertEqual(ugm.storage.keys(), [])

    @group_of_names_ugm
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
        self.assertEqual(user_0.attrs['login'], 'cn0')

        # XXX: LDAPNodeAttributes.items does not return consistent results if
        #      attrmap points to same attribute multiple times
        self.assertEqual(sorted(user_0.attrs.items()), [
            ('login', u'cn0'),
            ('mail', u'uid0@groupOfNames.com'),
            ('rdn', u'uid0'),
            ('sn', u'sn0')
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

    @group_of_names_ugm
    def test_authenticate(self, ugm):
        # Authenticate
        self.assertEqual(ugm.users.authenticate('uid0', 'secret0'), 'uid0')
        self.assertEqual(ugm.users.authenticate('cn0', 'secret0'), 'uid0')
        self.assertEqual(ugm.users.authenticate('uid0', 'invalid'), False)
        self.assertEqual(ugm.users.authenticate('cn0', 'invalid'), False)
        self.assertEqual(ugm.users.authenticate('foo', 'secret0'), False)

    @group_of_names_ugm
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

    @group_of_names_ugm
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
            sn='Bla',
            mail='baz@bar.com'
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

    @group_of_names_ugm
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
            ('member', [u'cn=nobody']),
            ('rdn', u'group0')
        ])
        self.assertEqual(sorted(group_1.attrs.items()), [
            ('member', [u'cn=nobody', u'uid=uid1,ou=users,ou=groupOfNames,dc=my-domain,dc=com']),
            ('rdn', u'group1')
        ])

    @group_of_names_ugm
    def test_add_group(self, ugm):
        groups = ugm.groups
        group = groups.create('group99', id='group99')
        self.assertTrue(isinstance(group, Group))

        ugm()
        self.check_output("""
        <class 'node.ext.ldap.ugm._api.Groups'>: groups
          <class 'node.ext.ldap.ugm._api.Group'>: group0
          <class 'node.ext.ldap.ugm._api.Group'>: group1
            <class 'node.ext.ldap.ugm._api.User'>: uid1
          <class 'node.ext.ldap.ugm._api.Group'>: group2
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
          <class 'node.ext.ldap.ugm._api.Group'>: group1
            <class 'node.ext.ldap.ugm._api.User'>: uid1
          <class 'node.ext.ldap.ugm._api.Group'>: group2
            <class 'node.ext.ldap.ugm._api.User'>: uid1
            <class 'node.ext.ldap.ugm._api.User'>: uid2
        """, groups.treerepr())

    @group_of_names_ugm
    def test_group_memebership(self, ugm):
        users = ugm.users
        groups = ugm.groups

        # A group returns the members ids as keys
        group_0 = groups['group0']
        group_1 = groups['group1']
        group_2 = groups['group2']

        self.assertEqual(group_0.member_ids, [])
        self.assertEqual(group_1.member_ids, ['uid1'])
        self.assertEqual(group_2.member_ids, ['uid1', 'uid2'])

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
        group_1.add('uid0')
        self.assertEqual(group_1.keys(), [u'uid1', u'uid0'])
        self.assertEqual(group_1.member_ids, [u'uid1', u'uid0'])
        self.assertTrue(group_1['uid0'] is ugm.users['uid0'])
        self.assertEqual(group_1.users, [users['uid1'], users['uid0']])

        group_1()

        # Let's take a fresh view on ldap whether this really happened
        ugm_fresh = create_ugm()
        self.assertEqual(ugm_fresh.groups['group1'].keys(), [u'uid1', u'uid0'])

        # Members are removed via ``delitem``
        del group_1['uid0']
        ugm_fresh = create_ugm()
        self.assertEqual(ugm_fresh.groups['group1'].keys(), [u'uid1'])

        user_0 = ugm_fresh.users['uid0']
        user_1 = ugm_fresh.users['uid1']
        user_2 = ugm_fresh.users['uid2']

        # A user knows its groups
        self.assertEqual(user_0.groups, [])
        self.assertEqual(user_1.groups, [
            ugm_fresh.groups['group1'],
            ugm_fresh.groups['group2']
        ])
        self.assertEqual(user_2.groups, [
            ugm_fresh.groups['group2']
        ])
        self.assertEqual(user_1.group_ids, [u'group1', u'group2'])
        self.assertEqual(user_2.group_ids, [u'group2'])

    @group_of_names_ugm
    def test_search(self, ugm):
        users = ugm.users
        groups = ugm.groups

        # Test search function
        self.assertEqual(users.search(criteria={'login': 'cn0'}), [u'uid0'])
        self.assertEqual(groups.search(criteria={'id': 'group2'}), [u'group2'])

    @group_of_names_ugm
    def test_ids(self, ugm):
        users = ugm.users
        groups = ugm.groups

        # There's an ids property on principals base class
        self.assertEqual(users.ids, [u'uid0', u'uid1', u'uid2'])
        self.assertEqual(groups.ids, [u'group0', u'group1', u'group2'])

    @group_of_names_ugm
    def test_membership_assignment(self, ugm):
        users = ugm.users
        groups = ugm.groups

        # Add user to some groups and then delete user, check whether user
        # is removed from all this groups.
        user = users.create(
            'sepp',
            cn='Sepp',
            sn='Bla',
            mail='baz@bar.com'
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
            <class 'node.ext.ldap.ugm._api.Group'>: group1
              <class 'node.ext.ldap.ugm._api.User'>: sepp
              <class 'node.ext.ldap.ugm._api.User'>: uid1
            <class 'node.ext.ldap.ugm._api.Group'>: group2
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
            <class 'node.ext.ldap.ugm._api.Group'>: group1
              <class 'node.ext.ldap.ugm._api.User'>: uid1
            <class 'node.ext.ldap.ugm._api.Group'>: group2
              <class 'node.ext.ldap.ugm._api.User'>: uid1
              <class 'node.ext.ldap.ugm._api.User'>: uid2
        """, ugm.treerepr())

    @group_of_names_ugm
    def test_member_of_support(self, ugm):
        users = ugm.users
        groups = ugm.groups

        self.assertEqual(users.context.search(queryFilter='(memberOf=*)'), [
            u'uid=uid1,ou=users,ou=groupOfNames,dc=my-domain,dc=com',
            u'uid=uid2,ou=users,ou=groupOfNames,dc=my-domain,dc=com'
        ])

        self.assertEqual(users.context.search(attrlist=['memberOf']), [
            (u'uid=uid0,ou=users,ou=groupOfNames,dc=my-domain,dc=com', {}),
            (u'uid=uid1,ou=users,ou=groupOfNames,dc=my-domain,dc=com', {
                u'memberOf': [
                    u'cn=group2,ou=groups,ou=groupOfNames,dc=my-domain,dc=com',
                    u'cn=group3,ou=altGroups,ou=groupOfNames,dc=my-domain,dc=com',
                    u'cn=group1,ou=groups,ou=groupOfNames,dc=my-domain,dc=com'
                ]
            }),
            (u'uid=uid2,ou=users,ou=groupOfNames,dc=my-domain,dc=com', {
                u'memberOf': [
                    u'cn=group2,ou=groups,ou=groupOfNames,dc=my-domain,dc=com',
                    u'cn=group3,ou=altGroups,ou=groupOfNames,dc=my-domain,dc=com'
                ]
            })
        ])

        ugm.ucfg.memberOfSupport = True
        ugm.gcfg.memberOfSupport = True

        self.assertEqual(users['uid1'].groups, [groups['group2'], groups['group1']])
        self.assertEqual(users['uid1'].group_ids, [u'group2', u'group1'])
        self.assertEqual(groups['group1'].member_ids, [u'uid1'])
        self.assertEqual(groups['group2'].member_ids, [u'uid1', u'uid2'])

        # test ugm tree external groups

        ugm.ucfg.memberOfExternalGroupDNs = ["ou=altGroups,ou=groupOfNames,dc=my-domain,dc=com"]
        ugm.gcfg.memberOfExternalGroupDNs = ["ou=altGroups,ou=groupOfNames,dc=my-domain,dc=com"]

        # external can not be handled by this ugm tree
        self.assertNotIn('group3', groups)

        self.assertEqual(users['uid1'].groups, [groups['group2'], groups['group1']])

        # but they are listed in group_ids
        self.assertEqual(
            sorted(users['uid1'].group_ids),
            [u"group1", u'group2', u'group3'],
        )
        self.assertEqual(groups['group1'].member_ids, [u'uid1'])
        self.assertEqual(groups['group2'].member_ids, [u'uid1', u'uid2'])


        ugm.ucfg.memberOfSupport = False
        ugm.gcfg.memberOfSupport = False
