from node.ext.ldap import testing
from node.tests import NodeTestCase
from node.ext.ldap.ugm import Ugm
from node.ext.ldap.ugm import Users
from node.ext.ldap.ugm import User
from node.ext.ldap.ugm import Groups
from node.ext.ldap.ugm._api import PrincipalAliasedAttributes
import ldap


layer = testing.LDIF_groupOfNames


def group_of_names_ugm(fn):
    def wrapper(self):
        props = layer['props']
        ucfg = layer['ucfg']
        gcfg = layer['gcfg']
        rcfg = None  # XXX: later
        ugm = Ugm(
            name='ugm',
            parent=None,
            props=props,
            ucfg=ucfg,
            gcfg=gcfg,
            rcfg=rcfg
        )
        fn(self, ugm)
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
        #      attrmap points to same attribute twice ('login' missing here)
        self.assertEqual(sorted(user_0.attrs.items()), [
            ('cn', u'cn0'),
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
        self.assertEqual(str(err), 'User does not implement ``__setitem__``')
        err = self.expect_error(
            NotImplementedError,
            user_0.__delitem__,
            'foo'
        )
        self.assertEqual(str(err), 'User does not implement ``__delitem__``')
        err = self.expect_error(
            NotImplementedError,
            user_0.__getitem__,
            'foo'
        )
        self.assertEqual(str(err), 'User does not implement ``__getitem__``')
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
        self.assertEqual(err.message, {
            'info': 'unwilling to verify old password',
            'desc': 'Server is unwilling to perform'
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

"""
Groups object::

    >>> groups = ugm.groups
    >>> groups.keys()
    [u'group0', u'group1', u'group2']

    >>> group_0 = groups['group0']
    >>> group_1 = groups['group1']
    >>> group_2 = groups['group2']

    >>> group_0
    <Group object 'group0' at ...>

    >>> group_0.__class__
    <class 'node.ext.ldap.ugm._api.Group'>

    >>> group_0.attrs
    Aliased <LDAPNodeAttributes object 'cn=group0' at ...>

    >>> group_0.attrs.items()
    [('member', [u'cn=nobody']), ('rdn', u'group0')]

    >>> group_1.attrs.items()
    [('member', [u'cn=nobody', u'uid=uid1,ou=users,ou=groupOfNames,dc=my-domain,dc=com']), 
    ('rdn', u'group1')]

Add a group::

    >>> group = groups.create('group99', id='group99')
    >>> group
    <Group object 'group99' at ...>

    >>> ugm()
    >>> ugm.printtree()
    <class 'node.ext.ldap.ugm._api.Ugm'>: ugm
      <class 'node.ext.ldap.ugm._api.Users'>: users
        <class 'node.ext.ldap.ugm._api.User'>: uid0
        <class 'node.ext.ldap.ugm._api.User'>: uid1
        <class 'node.ext.ldap.ugm._api.User'>: uid2
        <class 'node.ext.ldap.ugm._api.User'>: sepp
      <class 'node.ext.ldap.ugm._api.Groups'>: groups
        <class 'node.ext.ldap.ugm._api.Group'>: group0
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: uid1
        <class 'node.ext.ldap.ugm._api.Group'>: group2
          <class 'node.ext.ldap.ugm._api.User'>: uid1
          <class 'node.ext.ldap.ugm._api.User'>: uid2
        <class 'node.ext.ldap.ugm._api.Group'>: group99

    >>> ugm.groups['group99']
    <Group object 'group99' at ...>

A group returns the members ids as keys::

    >>> group_0.member_ids
    []

    >> group_1.member_ids
    [u'uid1']

    >> group_2.member_ids
    [u'uid1', u'uid2']

The member users are fetched via ``__getitem__``::

    >>> group_1['uid1']
    <User object 'uid1' at ...>

    >>> group_1['uid1'] is user_1
    True

Querying a group for a non-member results in a KeyError::

    >>> group_0['uid1']
    Traceback (most recent call last):
      ...
    KeyError: u'uid1'

Deleting inexistend member from group fails::

    >>> del group_0['inexistent']
    Traceback (most recent call last):
      ...
    KeyError: u'inexistent'

``__setitem__`` is prohibited::

    >>> group_1['uid0'] = users['uid0']
    Traceback (most recent call last):
      ...
    NotImplementedError: Group does not implement ``__setitem__``

Members are added via ``add``::

    >>> group_1.add('uid0')
    >>> group_1.keys()
    [u'uid1', u'uid0']

    >>> group_1.member_ids
    [u'uid1', u'uid0']

    >>> group_1['uid0']
    <User object 'uid0' at ...>

    >>> group_1.users
    [<User object 'uid1' at ...>, <User object 'uid0' at ...>]

    >>> group_1()

Let's take a fresh view on ldap whether this really happened::

    >>> ugm_fresh = Ugm(name='ugm', parent=None, props=props,
    ...                 ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)
    >>> ugm_fresh.groups['group1'].keys()
    [u'uid1', u'uid0']

Members are removed via ``delitem``::

    >>> del group_1['uid0']
    >>> ugm_fresh = Ugm(name='ugm', parent=None, props=props,
    ...                 ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)
    >>> ugm_fresh.groups['group1'].keys()
    [u'uid1']

A user knows its groups::

    >>> user_0.groups
    []

    >>> user_1.groups
    [<Group object 'group1' at ...>, <Group object 'group2' at ...>]

    >>> user_2.groups
    [<Group object 'group2' at ...>]

    >>> user_1.group_ids
    [u'group1', u'group2']

    >>> user_2.group_ids
    [u'group2']

Recreate UGM object::

    >>> ugm = Ugm(name='ugm', parent=None, props=props,
    ...           ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)
    >>> users = ugm.users
    >>> groups = ugm.groups

Test search function::

    >>> users.search(criteria={'login': 'cn0'})
    [u'uid0']

    >>> groups.search(criteria={'id': 'group2'})
    [u'group2']

There's an ids property on principals base class::

    >>> users.ids
    [u'uid0', u'uid1', u'uid2', u'sepp']

    >>> groups.ids
    [u'group0', u'group1', u'group2', u'group99']

Add now user to some groups and then delete user, check whether user is removed
from all this groups.::

    >>> ugm = Ugm(name='ugm', parent=None, props=props,
    ...           ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)
    >>> users = ugm.users
    >>> groups = ugm.groups

    >>> groups['group0'].add('sepp')
    >>> groups['group1'].add('sepp')
    >>> ugm()

    >>> user.groups
    [<Group object 'group0' at ...>, <Group object 'group1' at ...>]

    >>> user.group_ids
    [u'group0', u'group1']

    >>> ugm.printtree()
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
        <class 'node.ext.ldap.ugm._api.Group'>: group99

    >>> del users['sepp']
    >>> ugm()
    >>> ugm.printtree()
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
        <class 'node.ext.ldap.ugm._api.Group'>: group99

Delete Group::

    >>> del groups['group99']
    >>> ugm()
    >>> ugm.printtree()
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

MemberOf Support::

    >>> users = ugm.users
    >>> users.context.search(queryFilter='(memberOf=*)')
    [u'uid=uid1,ou=users,ou=groupOfNames,dc=my-domain,dc=com', 
    u'uid=uid2,ou=users,ou=groupOfNames,dc=my-domain,dc=com']

    >>> users.context.search(attrlist=['memberOf'])
    [(u'uid=uid0,ou=users,ou=groupOfNames,dc=my-domain,dc=com', {}),
    (u'uid=uid1,ou=users,ou=groupOfNames,dc=my-domain,dc=com', {u'memberOf':
    [u'cn=group2,ou=groups,ou=groupOfNames,dc=my-domain,dc=com',
    u'cn=group3,ou=altGroups,ou=groupOfNames,dc=my-domain,dc=com',
    u'cn=group1,ou=groups,ou=groupOfNames,dc=my-domain,dc=com']}),
    (u'uid=uid2,ou=users,ou=groupOfNames,dc=my-domain,dc=com', {u'memberOf':
    [u'cn=group2,ou=groups,ou=groupOfNames,dc=my-domain,dc=com',
    u'cn=group3,ou=altGroups,ou=groupOfNames,dc=my-domain,dc=com']})]

    >>> ugm.ucfg.memberOfSupport = True
    >>> ugm.gcfg.memberOfSupport = True

    >>> users['uid1'].groups
    [<Group object 'group2' at ...>, 
    <Group object 'group1' at ...>]

    >>> users['uid1'].group_ids
    [u'group2', u'group1']

    >>> groups['group1'].member_ids
    [u'uid1']

    >>> groups['group2'].member_ids
    [u'uid1', u'uid2']

    >>> ugm.ucfg.memberOfSupport = False
    >>> ugm.gcfg.memberOfSupport = False
"""