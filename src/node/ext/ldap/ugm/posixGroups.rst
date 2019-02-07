Tests refering to posixGroups.ldif
==================================

Test related imports::

    >>> from node.ext.ldap import LDAPNode
    >>> from node.ext.ldap import SUBTREE
    >>> from node.ext.ldap.ugm import RolesConfig
    >>> from node.ext.ldap.ugm import Ugm

Ugm root object::

    >>> props = layer['props']
    >>> ucfg = layer['ucfg']
    >>> gcfg = layer['gcfg']
    >>> rcfg = None # XXX: later

    >>> ugm = Ugm(name='ugm', parent=None, props=props,
    ...           ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)

    >>> ugm
    <Ugm object 'ugm' at ...>

Users object::

    >>> ugm.users
    <Users object 'users' at ...>

    >>> ugm['users'] is ugm.users
    True

Groups object::

    >>> ugm.groups
    <Groups object 'groups' at ...>

    >>> ugm['groups'] is ugm.groups
    True

Try to delete from UGM, fails::

    >>> del ugm['users']
    Traceback (most recent call last):
      ...
    NotImplementedError: Operation forbidden on this node.

Try to set item by invalid key, fails::

    >>> ugm['inexistent'] = ugm.users
    Traceback (most recent call last):
      ...
    KeyError: 'inexistent'

User keys::

    >>> users = ugm.users
    >>> users.keys()
    ['uid0', 'uid1', 'uid2']

Fetch some users::

    >>> user_0 = users['uid0']
    >>> user_1 = users['uid1']
    >>> user_2 = users['uid2']

    >>> user_0
    <User object 'uid0' at ...>

    >>> user_0.__class__
    <class 'node.ext.ldap.ugm._api.User'>

    >>> user_0.attrs
    Aliased <LDAPNodeAttributes object 'uid=uid0' at ...>

    >>> user_0.attrs['cn']
    'cn0'

    >>> user_0.attrs['sn']
    'sn0'

    >>> user_0.attrs['login']
    'cn0'

    >>> sorted(user_0.attrs.items())
    [('gidNumber', '0'), 
    ('homeDirectory', '/home/uid0'), 
    ('id', 'uid0'), 
    ('login', 'cn0'), 
    ('sn', 'sn0'), 
    ('uidNumber', '0')]

User is a leaf::

    >>> user_0['foo'] = object()
    Traceback (most recent call last):
      ...
    NotImplementedError: User does not implement ``__setitem__``

    >>> del user_0['foo']
    Traceback (most recent call last):
      ...
    NotImplementedError: User does not implement ``__delitem__``

    >>> user_0['foo']
    Traceback (most recent call last):
      ...
    NotImplementedError: User does not implement ``__getitem__``

    >>> user_0.keys()
    []

Authenticate no account expiration configured::

    >>> users.expiresAttr

    >>> users.authenticate('uid0', 'secret0')
    'uid0'

    >>> users.authenticate('cn0', 'secret0')
    'uid0'

    >>> users.authenticate('uid0', 'invalid')
    False

    >>> users.authenticate('cn0', 'invalid')
    False

    >>> users.authenticate('foo', 'secret0')
    False

Check Account expiration.

Note: after changind expires attribute, user must be pesisted in order to take
expiration effect for authentication. Expires attribute lookup is done against
LDAP directly in ``users.authenticate``::

Expires attribute not set yet::

    >>> users.expiresAttr
    >>> users['uid0'].expired
    False

Set expires attribute for ongoing tests::

    >>> users.expiresAttr = 'shadowExpire'

Value 99999 and -1 means no expiration::

    >>> users['uid0'].context.attrs['shadowExpire']
    '99999'

    >>> users['uid0'].context.attrs['shadowInactive']
    '0'

    >>> users.authenticate('uid0', 'secret0')
    'uid0'

    >>> users['uid0'].expired
    False

Expire a while ago::

    >>> users['uid0'].context.attrs['shadowExpire'] = '1'
    >>> users['uid0']()
 
    >>> res = users.authenticate('uid0', 'secret0')
    >>> res
    ACCOUNT_EXPIRED

    >>> bool(res)
    False

    >>> users['uid0'].expired
    True

No expiration far future::

    >>> users['uid0'].context.attrs['shadowExpire'] = '99999'
    >>> users['uid0']()
    >>> users.authenticate('uid0', 'secret0')
    'uid0'

    >>> users['uid0'].expired
    False

No expiration by '-1'::

    >>> users['uid0'].context.attrs['shadowExpire'] = '-1'
    >>> users['uid0']()
    >>> users.authenticate('uid0', 'secret0')
    'uid0'

    >>> users['uid0'].expired
    False

#### figure out shadowInactive -> PAM and samba seem to ignore -> configuration?

    >> users['uid0'].context.attrs['shadowInactive'] = '99999'

Uid0 never expires - or at leas expires in many years and even if, there are
99999 more days unless account gets disabled::

#    >> users.authenticate('uid0', 'secret0')
#    'uid0'

#    >> users['uid0'].context.attrs['shadowInactive'] = '0'

Change password::

    >>> users.passwd('uid0', 'foo', 'bar')
    Traceback (most recent call last):
      ...
    ldap.UNWILLING_TO_PERFORM: ...

    >>> users.passwd('foo', 'secret0', 'bar')
    Traceback (most recent call last):
      ...
    KeyError: 'foo'

    >>> users.passwd('uid0', 'secret0', 'bar')
    >>> users.authenticate('uid0', 'bar')
    'uid0'

Add user::

    >>> users.printtree()
    <class 'node.ext.ldap.ugm._api.Users'>: users
      <class 'node.ext.ldap.ugm._api.User'>: uid0
      <class 'node.ext.ldap.ugm._api.User'>: uid1
      <class 'node.ext.ldap.ugm._api.User'>: uid2

    >>> user = users.create('sepp',
    ...                     cn='Sepp',
    ...                     sn='Unterwurzacher',
    ...                     uidNumber='99',
    ...                     gidNumber='99',
    ...                     homeDirectory='home/sepp')
    >>> user
    <User object 'sepp' at ...>

The user is added to tree::

    >>> ugm.printtree()
    <class 'node.ext.ldap.ugm._api.Ugm'>: ugm
      <class 'node.ext.ldap.ugm._api.Users'>: users
        <class 'node.ext.ldap.ugm._api.User'>: uid0
        <class 'node.ext.ldap.ugm._api.User'>: uid1
        <class 'node.ext.ldap.ugm._api.User'>: uid2
        <class 'node.ext.ldap.ugm._api.User'>: sepp
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

Though, no authentication or password setting possible yet, because tree is
not persisted to LDAP yet::

    >>> users.authenticate('sepp', 'secret')
    False

    >>> ugm.users.passwd('sepp', None, 'secret')
    Traceback (most recent call last):
      ...
    KeyError: 'sepp'

After calling, new user is available in LDAP::

    >>> ugm()
    >>> ugm.users.passwd('sepp', None, 'secret')
    >>> users.authenticate('sepp', 'secret')
    'sepp'

Groups object::

    >>> groups = ugm.groups
    >>> groups.keys()
    ['group0', 'group1', 'group2']

    >>> group_0 = groups['group0']
    >>> group_1 = groups['group1']
    >>> group_2 = groups['group2']

    >>> group_0
    <Group object 'group0' at ...>

    >>> group_0.__class__
    <class 'node.ext.ldap.ugm._api.Group'>

    >>> group_0.attrs
    Aliased <LDAPNodeAttributes object 'cn=group0' at ...>

    >>> sorted(group_0.attrs.items())
    [('gidNumber', '0'), 
    ('id', 'group0'),
    ('memberUid', ['nobody', 'uid0'])]

    >>> sorted(group_1.attrs.items())
    [('gidNumber', '1'), 
    ('id', 'group1'),
    ('memberUid', ['nobody', 'uid0', 'uid1'])]

Add a group::

    >>> group = groups.create('group99', id='group99', gidNumber='99')
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
          <class 'node.ext.ldap.ugm._api.User'>: uid0
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: uid0
          <class 'node.ext.ldap.ugm._api.User'>: uid1
        <class 'node.ext.ldap.ugm._api.Group'>: group2
          <class 'node.ext.ldap.ugm._api.User'>: uid0
          <class 'node.ext.ldap.ugm._api.User'>: uid1
          <class 'node.ext.ldap.ugm._api.User'>: uid2
        <class 'node.ext.ldap.ugm._api.Group'>: group99

    >>> ugm.groups['group99']
    <Group object 'group99' at ...>

A group returns the members ids as keys::

    >>> group_0.member_ids
    ['uid0']

    >> group_1.member_ids
    ['uid1']

    >> group_2.member_ids
    ['uid1', 'uid2']

The member users are fetched via ``__getitem__``::

    >>> group_1['uid1']
    <User object 'uid1' at ...>

    >>> group_1['uid1'] is user_1
    True

Querying a group for a non-member results in a KeyError::

    >>> group_0['uid1']
    Traceback (most recent call last):
      ...
    KeyError: 'uid1'

Deleting inexistend member from group fails::

    >>> del group_0['inexistent']
    Traceback (most recent call last):
      ...
    KeyError: 'inexistent'

``__setitem__`` is prohibited::

    >>> group_1['uid0'] = users['uid0']
    Traceback (most recent call last):
      ...
    NotImplementedError: Group does not implement ``__setitem__``

Members are added via ``add``::

    >>> group_1.add('uid0')
    >>> group_1.keys()
    ['uid0', 'uid1']

    >>> group_1.member_ids
    ['uid0', 'uid1']

    >>> group_1['uid0']
    <User object 'uid0' at ...>

    >>> group_1.users
    [<User object 'uid0' at ...>, <User object 'uid1' at ...>]

    >>> group_1()

Let's take a fresh view on ldap whether this really happened::

    >>> ugm_fresh = Ugm(name='ugm', parent=None, props=props,
    ...                 ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)
    >>> ugm_fresh.groups['group1'].keys()
    ['uid0', 'uid1']

Members are removed via ``delitem``::

    >>> del group_1['uid0']
    >>> ugm_fresh = Ugm(name='ugm', parent=None, props=props,
    ...                 ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)
    >>> ugm_fresh.groups['group1'].keys()
    ['uid1']

    >>> ugm.printtree()
    <class 'node.ext.ldap.ugm._api.Ugm'>: ugm
      <class 'node.ext.ldap.ugm._api.Users'>: users
        <class 'node.ext.ldap.ugm._api.User'>: uid0
        <class 'node.ext.ldap.ugm._api.User'>: uid1
        <class 'node.ext.ldap.ugm._api.User'>: uid2
        <class 'node.ext.ldap.ugm._api.User'>: sepp
      <class 'node.ext.ldap.ugm._api.Groups'>: groups
        <class 'node.ext.ldap.ugm._api.Group'>: group0
          <class 'node.ext.ldap.ugm._api.User'>: uid0
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: uid1
        <class 'node.ext.ldap.ugm._api.Group'>: group2
          <class 'node.ext.ldap.ugm._api.User'>: uid0
          <class 'node.ext.ldap.ugm._api.User'>: uid1
          <class 'node.ext.ldap.ugm._api.User'>: uid2
        <class 'node.ext.ldap.ugm._api.Group'>: group99

A user knows its groups::

    >>> user_0.groups
    [<Group object 'group0' at ...>, <Group object 'group2' at ...>]

    >>> user_1.groups
    [<Group object 'group1' at ...>, <Group object 'group2' at ...>]

    >>> user_2.groups
    [<Group object 'group2' at ...>]

    >>> user_0.group_ids
    ['group0', 'group2']

    >>> user_1.group_ids
    ['group1', 'group2']

    >>> user_2.group_ids
    ['group2']

Recreate UGM object::

    >>> ugm = Ugm(name='ugm', parent=None, props=props,
    ...           ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)
    >>> users = ugm.users
    >>> groups = ugm.groups

Test search function::

    >>> users.search(criteria={'login': 'cn0'})
    ['uid0']

    >>> groups.search(criteria={'id': 'group2'})
    ['group2']

There's an ids property on principals base class::

    >>> users.ids
    ['uid0', 'uid1', 'uid2', 'sepp']

    >>> groups.ids
    ['group0', 'group1', 'group2', 'group99']

Add now user to some groups and then delete user, check whether user is removed
from all this groups::

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
    ['group0', 'group1']

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
          <class 'node.ext.ldap.ugm._api.User'>: uid0
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: sepp
          <class 'node.ext.ldap.ugm._api.User'>: uid1
        <class 'node.ext.ldap.ugm._api.Group'>: group2
          <class 'node.ext.ldap.ugm._api.User'>: uid0
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
          <class 'node.ext.ldap.ugm._api.User'>: uid0
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: uid1
        <class 'node.ext.ldap.ugm._api.Group'>: group2
          <class 'node.ext.ldap.ugm._api.User'>: uid0
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
          <class 'node.ext.ldap.ugm._api.User'>: uid0
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: uid1
        <class 'node.ext.ldap.ugm._api.Group'>: group2
          <class 'node.ext.ldap.ugm._api.User'>: uid0
          <class 'node.ext.ldap.ugm._api.User'>: uid1
          <class 'node.ext.ldap.ugm._api.User'>: uid2

Test case where group object does not have 'memberUid' attribute set yet.::

    >>> node = LDAPNode(
    ...     'cn=group0,ou=groups,ou=posixGroups,dc=my-domain,dc=com',
    ...     props=props)

    >>> del node.attrs['memberUid']
    >>> node()

    >>> ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg)
    >>> group = ugm.groups['group0']
    >>> group.items()
    []

    >>> group.add('uid0')
    >>> group()

Test case where group contains reference to inexistent member.::

    >>> node.attrs['memberUid'] = ['uid1', 'inexistent']
    >>> node()

    >>> ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg)
    >>> group = ugm.groups['group0']
    >>> group.items()
    [('uid1', <User object 'uid1' at ...>)]

Role Management. Create container for roles.::

    >>> node = LDAPNode('dc=my-domain,dc=com', props)
    >>> node['ou=roles'] = LDAPNode()
    >>> node['ou=roles'].attrs['objectClass'] = ['organizationalUnit']
    >>> node()

    >>> from odict import odict
    >>> rcfg = RolesConfig(
    ...     baseDN='ou=roles,dc=my-domain,dc=com',
    ...     attrmap=odict((
    ...         ('id', 'cn'),
    ...         ('rdn', 'cn'),
    ...     )),
    ...     scope=SUBTREE,
    ...     queryFilter='(objectClass=posixGroup)',
    ...     objectClasses=['posixGroup'],
    ...     defaults={},
    ...     strict=False,
    ... )

    >>> ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)

    >>> user = ugm.users['uid1']
    >>> ugm.roles(user)
    []

    >>> ugm.add_role('viewer', user)
    >>> ugm.roles(user)
    ['viewer']

    >>> user.roles
    ['viewer']

    >>> user = ugm.users['uid2']
    >>> user.add_role('viewer')
    >>> user.add_role('editor')
    >>> sorted(user.roles)
    ['editor', 'viewer']

    >>> ugm.roles_storage()

    >>> ugm.remove_role('viewer', user)
    >>> user.remove_role('editor')
    >>> user.roles
    []

    >>> ugm.roles_storage()

    >>> group = ugm.groups['group1']
    >>> ugm.roles(group)
    []

    >>> ugm.add_role('viewer', group)

    >>> ugm.roles(group)
    ['viewer']

    >>> group.roles
    ['viewer']

    >>> group = ugm.groups['group0']
    >>> group.add_role('viewer')
    >>> group.add_role('editor')

    >>> group.roles
    ['viewer', 'editor']

    >>> ugm.roles_storage()

    >>> group.add_role('editor')
    Traceback (most recent call last):
      ...
    ValueError: Principal already has role 'editor'

    >>> ugm.remove_role('viewer', group)

    >>> ugm.roles_storage.keys()
    ['viewer', 'editor']

    >>> group.remove_role('editor')

    >>> ugm.roles_storage.keys()
    ['viewer']

    >>> ugm.roles_storage.storage.keys()
    ['viewer']

    >>> ugm.roles_storage['editor']
    Traceback (most recent call last):
      ...
    KeyError: 'editor'

    >>> group.remove_role('editor')
    Traceback (most recent call last):
      ...
    ValueError: Role not exists 'editor'

    >>> group.remove_role('viewer')
    Traceback (most recent call last):
      ...
    ValueError: Principal does not has role 'viewer'

    >>> ugm.roles_storage()
