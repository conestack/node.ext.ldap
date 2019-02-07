Tests refering to groupOfNames.ldif
===================================

Test related imports::

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

    >>> user_0.attrs['login']
    'cn0'

XXX: LDAPNodeAttributes.items does not return consistent results if attrmap
     points to same attribute twice ('login' missing here)

::

    >>> sorted(user_0.attrs.values())
    ['cn0', 
     'sn0',
     'uid0',
     'uid0@groupOfNames.com']

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

Authenticate::

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
    ...                     sn='Bla',
    ...                     mail='baz@bar.com')

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
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: uid1
        <class 'node.ext.ldap.ugm._api.Group'>: group2
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
    [('id', 'group0'), ('member', ['cn=nobody'])]

    >>> sorted(group_1.attrs.items())
    [('id', 'group1'),
    ('member', ['cn=nobody', 'uid=uid1,ou=users,ou=groupOfNames,dc=my-domain,dc=com'])]

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
    ['uid1', 'uid0']

    >>> group_1.member_ids
    ['uid1', 'uid0']

    >>> group_1['uid0']
    <User object 'uid0' at ...>

    >>> group_1.users
    [<User object 'uid1' at ...>, <User object 'uid0' at ...>]

    >>> group_1()

Let's take a fresh view on ldap whether this really happened::

    >>> ugm_fresh = Ugm(name='ugm', parent=None, props=props,
    ...                 ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)
    >>> ugm_fresh.groups['group1'].keys()
    ['uid1', 'uid0']

Members are removed via ``delitem``::

    >>> del group_1['uid0']
    >>> ugm_fresh = Ugm(name='ugm', parent=None, props=props,
    ...                 ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)
    >>> ugm_fresh.groups['group1'].keys()
    ['uid1']

A user knows its groups::

    >>> user_0.groups
    []

    >>> user_1.groups
    [<Group object 'group1' at ...>, <Group object 'group2' at ...>]

    >>> user_2.groups
    [<Group object 'group2' at ...>]

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
    ['uid=uid1,ou=users,ou=groupOfNames,dc=my-domain,dc=com', 
    'uid=uid2,ou=users,ou=groupOfNames,dc=my-domain,dc=com']

    >>> users.context.search(attrlist=['memberOf'])
    [('uid=uid0,ou=users,ou=groupOfNames,dc=my-domain,dc=com', {}),
    ('uid=uid1,ou=users,ou=groupOfNames,dc=my-domain,dc=com', {'memberOf':
    ['cn=group2,ou=groups,ou=groupOfNames,dc=my-domain,dc=com',
    'cn=group3,ou=altGroups,ou=groupOfNames,dc=my-domain,dc=com',
    'cn=group1,ou=groups,ou=groupOfNames,dc=my-domain,dc=com']}),
    ('uid=uid2,ou=users,ou=groupOfNames,dc=my-domain,dc=com', {'memberOf':
    ['cn=group2,ou=groups,ou=groupOfNames,dc=my-domain,dc=com',
    'cn=group3,ou=altGroups,ou=groupOfNames,dc=my-domain,dc=com']})]

    >>> ugm.ucfg.memberOfSupport = True
    >>> ugm.gcfg.memberOfSupport = True

    >>> users['uid1'].groups
    [<Group object 'group2' at ...>, 
    <Group object 'group1' at ...>]

    >>> users['uid1'].group_ids
    ['group2', 'group1']

    >>> groups['group1'].member_ids
    ['uid1']

    >>> groups['group2'].member_ids
    ['uid1', 'uid2']

    >>> ugm.ucfg.memberOfSupport = False
    >>> ugm.gcfg.memberOfSupport = False
