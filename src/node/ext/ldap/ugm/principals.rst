# -*- coding: utf-8 -*-

Create a LDAPUsers node and configure it. In addition to the key attribute, the
login attribute also needs to be unique, which will be checked upon calling
ids() the first time::

    >>> from node.ext.ldap.ugm import Users, UsersConfig
    >>> from node.ext.ldap import ONELEVEL

    >>> from node.ext.ldap.testing import props, ucfg
    >>> ucfg.attrmap
    {'telephoneNumber': 'telephoneNumber', 
    'login': 'description', 
    'rdn': 'ou', 
    'id': 'sn', 
    'sn': 'sn'}

Query all user ids. ``description`` is set as login attribute and is missing
on some::

    >>> users = Users(props, ucfg)
    Traceback (most recent call last):
    ...
    KeyError:
      u"Secondary key 'description' missing on: cn=user1,dc=my-domain,dc=com."

Query all user ids. Set ``telephoneNumber`` as login attribute, which is not
unique::

    >>> ucfg.attrmap['login'] = 'telephoneNumber'
    >>> users = Users(props, ucfg)
    Traceback (most recent call last):
    ...
    KeyError: u"Secondary key not unique: telephoneNumber='1234'."

Query all user ids. Set ``cn`` as login attribute. In this case, values are
unique and therefore suitable as login attr::

    >>> ucfg.attrmap['login'] = 'cn'
    >>> users = Users(props, ucfg)
    >>> users.ids
    [u'Meier', u'M\xfcller', u'Schmidt', u'Umhauer']

Principals idbydn::

    >>> users.idbydn('cn=user3,ou=customers,dc=my-domain,dc=com')
    u'Schmidt'
    
    >>> users.idbydn('cN=user3, ou=customers,dc=MY-domain,dc= com')
    u'Schmidt'
    
    >>> users.idbydn('cN=inexistent, ou=customers,dc=MY-domain,dc= com')
    Traceback (most recent call last):
      ...
    KeyError: 'cN=inexistent, ou=customers,dc=MY-domain,dc= com'

Get a user by id (utf-8 or unicode)::

    >>> mueller = users['Müller']
    >>> mueller
    <User object 'M?ller' at ...>

    >>> mueller is users['Müller']
    True

The real LDAP node is on ``context``::

    >>> mueller.context
    <cn=user2,ou=customers,dc=my-domain,dc=com:M?ller - False>

The '?' is just ``__repr__`` going to ascii, the id is in proper unicode::

    >>> mueller.id
    u'M\xfcller'

A user has a login::

    >>> mueller.login
    u'user2'

And attributes::

    >>> mueller.attrs
    Aliased <LDAPNodeAttributes object 'M?ller' at ...>
    
    >>> mueller.attrs.items()
    [('telephoneNumber', u'1234'), ('login', u'user2'), ('id', u'M\xfcller')]

Query all user nodes::

    >>> [users[id] for id in users]
    [<User object 'Meier' at ...>, 
    <User object 'M?ller' at ...>, 
    <User object 'Schmidt' at ...>, 
    <User object 'Umhauer' at ...>]
    
    >>> [users[id].context for id in users]
    [<cn=user1,dc=my-domain,dc=com:Meier - False>,
    <cn=user2,ou=customers,dc=my-domain,dc=com:M?ller - False>,
    <cn=user3,ou=customers,dc=my-domain,dc=com:Schmidt - False>,
    <cn=n?sty\2C User,ou=Customers,dc=My-Domain,dc=com:Umhauer - False>]

Authenticate a user, via the user object. (also see 'via LDAPUsers' below,
after passwd, this is to make sure, that LDAPUsers.authenticate does not work
on a cached copy)::

    >>> mueller.authenticate('foo2')
    True
    
    >>> mueller.authenticate('bar')
    False

Change a users password, supplying the old password, via the user object::

    >>> oldpw = 'foo2'
    >>> newpw = 'new'
    >>> mueller.passwd(oldpw, newpw)
    >>> mueller.authenticate('foo2')
    False
    
    >>> mueller.authenticate('new')
    True

And via LDAPUsers::

    >>> oldpw = newpw
    >>> newpw = 'newer'
    >>> users.passwd(mueller.id, oldpw, newpw)

Authenticate a user via LDAPUsers, either by id or by login, but not both. The
id is returned if sucessful, otherwise None::

    >>> users.authenticate('wrong', 'creds')
    False

    >>> users.authenticate(mueller.login, 'newer')
    u'M\xfcller'

    >>> print users.authenticate(id='wrong', pw='cresd')
    False
    
    >>> print users.authenticate(id=mueller.id, pw='bar')
    False
    
    >>> users.authenticate(id=mueller.id, pw='newer')
    u'M\xfcller'

Create new User. Provide some user defaults in user configuration. A default
is either the desired value or a callback accepting the principals node and the
id and returns the desired value.::

    >>> from node.ext.ldap import ONELEVEL
    >>> def telephoneNumberDefault(node, id):
    ...     # default value callback function
    ...     return '123'
    
    >>> add_ucfg = UsersConfig(
    ...     baseDN='ou=customers,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'sn',
    ...         'login': 'cn',
    ...         'rdn': 'cn',
    ...         'telephoneNumber': 'telephoneNumber',
    ...         'sn': 'sn',
    ...      },
    ...     scope=ONELEVEL,
    ...     queryFilter='(objectClass=person)',
    ...     objectClasses=['top', 'person'],
    ...     defaults={
    ...         'sn': 'Surname',
    ...         'telephoneNumber': telephoneNumberDefault,
    ...     },
    ... )
    >>> users = Users(props, add_ucfg)

    >>> users.ids
    [u'M\xfcller', u'Schmidt', u'Umhauer']

    >>> users.create('newid')
    Traceback (most recent call last):
      ...
    ValueError: 'cn' needed in node attributes for rdn.

    >>> users.create('newid', login='newcn', id='newid')
    <User object 'newid' at ...>
    
    >>> users.ids
    [u'M\xfcller', u'Schmidt', u'Umhauer', u'newid']

    >>> newuser = users['newid']
    >>> newuser.context
    <cn=newcn,ou=customers,dc=my-domain,dc=com:newid - True>

Create function uses __setitem__ for adding new members. You can use this as
well, but create is propably the better choice. Test egde cases::

    >>> from node.base import BaseNode
    >>> node = BaseNode()
    >>> users['foo'] = node
    Traceback (most recent call last):
      ...
    ValueError: no attributes found, cannot convert.
    
    >>> from node.base import AttributedNode
    >>> node = AttributedNode()
    >>> users['newid'] = node
    Traceback (most recent call last):
      ...
    KeyError: u"Key already exists: 'newid'."

# XXX: there need more attrs to show up::

    >>> newuser.attrs.items()
    [('login', u'newcn'), ('id', u'newid'), ('telephoneNumber', u'123')]
    
    >>> newuser.context.attrs.items()
    [(u'cn', u'newcn'), 
    (u'sn', u'newid'), 
    (u'objectClass', ['top', 'person']), 
    (u'telephoneNumber', u'123')]
    
    >>> users()
    >>> users.reload = True

    >>> users.items()
    [(u'M\xfcller', <User object 'M?ller' at ...>), 
    (u'Schmidt', <User object 'Schmidt' at ...>), 
    (u'Umhauer', <User object 'Umhauer' at ...>), 
    (u'newid', <User object 'newid' at ...>)]

    >>> users['newid'].context
    <cn=newcn,ou=customers,dc=my-domain,dc=com:newid - False>

Delete User::

    >>> del users['newid']
    >>> users.context()

Search for users::

    >>> users = Users(props, ucfg)
    >>> schmidt = users['Schmidt']
    >>> users.search(criteria=dict(sn=schmidt.attrs['sn']), exact_match=True)
    [u'Schmidt']

    >>> users.search()
    [u'Meier', u'M\xfcller', u'Schmidt', u'Umhauer']

    >>> users.search(attrlist=['login'])
    [(u'Meier', {'login': [u'user1']}), 
    (u'M\xfcller', {'login': [u'user2']}), 
    (u'Schmidt', {'login': [u'user3']}), 
    (u'Umhauer', {'login': [u'n\xe4sty, User']})]
    
    >>> users.search(criteria=dict(sn=schmidt.attrs['sn']), attrlist=['login'])
    [(u'Schmidt', {'login': [u'user3']})]

Only attributes defined in attrmap can be queried::

    >>> users.search(criteria=dict(sn=schmidt.attrs['sn']),
    ...                            attrlist=['description'])
    Traceback (most recent call last):
    ...
    KeyError: 'description'
    
    >>> users.search(criteria=dict(sn=schmidt.attrs['sn']),
    ...                            attrlist=['telephoneNumber'])
    [(u'Schmidt', {'telephoneNumber': [u'1234']})]

    >>> from node.ext.ldap.filter import LDAPFilter
    >>> filter = LDAPFilter('(objectClass=person)')
    >>> filter |= LDAPFilter('(objectClass=some)')
    
    # normally set via principals config
    >>> users.context.search_filter = filter
    >>> users.search()
    [u'Meier', u'M\xfcller', u'Schmidt', u'Umhauer']
    
    >>> filter = LDAPFilter('(objectClass=person)')
    >>> filter &= LDAPFilter('(objectClass=some)')
    
    # normally set via principals config
    >>> users.context.search_filter = filter
    >>> users.search()
    []
    
    >>> users.context.search_filter = None

The changed flag::

    >>> users.changed
    False
    
    >>> users.printtree()
    <class 'node.ext.ldap.ugm._api.Users'>: None
      <class 'node.ext.ldap.ugm._api.User'>: Meier
      <class 'node.ext.ldap.ugm._api.User'>: M?ller
      <class 'node.ext.ldap.ugm._api.User'>: Schmidt
      <class 'node.ext.ldap.ugm._api.User'>: Umhauer
    
    >>> users.context.printtree()
    <dc=my-domain,dc=com - False>
      <cn=user1,dc=my-domain,dc=com:Meier - False>
      <cn=user2,ou=customers,dc=my-domain,dc=com:M?ller - False>
      <cn=user3,ou=customers,dc=my-domain,dc=com:Schmidt - False>
      <cn=n?sty\2C User,ou=Customers,dc=My-Domain,dc=com:Umhauer - False>
    
    >>> users['Meier'].attrs['telephoneNumber'] = '12345'
    >>> users['Meier'].attrs.changed
    True
    
    >>> users['Meier'].changed
    True
    
    >>> users.changed
    True
    
    >>> users.context.printtree()
    <dc=my-domain,dc=com - True>
      <cn=user1,dc=my-domain,dc=com:Meier - True>
      <cn=user2,ou=customers,dc=my-domain,dc=com:M?ller - False>
      <cn=user3,ou=customers,dc=my-domain,dc=com:Schmidt - False>
      <cn=n?sty\2C User,ou=Customers,dc=My-Domain,dc=com:Umhauer - False>
    
    >>> users['Meier'].attrs.context.load()
    >>> users['Meier'].attrs.changed
    False
    
    >>> users['Meier'].changed
    False
    
    >>> users.changed
    False
    
    >>> users.context.printtree()
    <dc=my-domain,dc=com - False>
      <cn=user1,dc=my-domain,dc=com:Meier - False>
      <cn=user2,ou=customers,dc=my-domain,dc=com:M?ller - False>
      <cn=user3,ou=customers,dc=my-domain,dc=com:Schmidt - False>
      <cn=n?sty\2C User,ou=Customers,dc=My-Domain,dc=com:Umhauer - False>

A user does not know about it's groups if initialized directly::

    >>> users['Meier'].groups
    Traceback (most recent call last):
      ...
    AttributeError: 'NoneType' object has no attribute 'groups'

Create a LDAPGroups node and configure it::

    >>> from node.ext.ldap.ugm import Groups, GroupsConfig
    >>> gcfg = GroupsConfig(
    ...     baseDN='dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'cn',
    ...         'rdn': 'cn',
    ...     },
    ...     scope=ONELEVEL,
    ...     queryFilter='(objectClass=groupOfNames)',
    ...     objectClasses=['groupOfNames'],
    ... )

    >>> groups = Groups(props, gcfg)
    >>> groups.keys()
    [u'group1', u'group2']
    
    >>> groups.ids
    [u'group1', u'group2']
    
    >>> group = groups['group1']
    >>> group
    <Group object 'group1' at ...>
    
    >>> group = groups.create('group3')
    >>> groups()
    >>> groups.ids
    [u'group1', u'group2', u'group3']
    
    # XXX: dummy member should be created by default value callback, currently
    #      a __setitem__ plumbing on groups object
    
    >>> groups.context.ldap_session.search(queryFilter='cn=group3',
    ...                                    scope=ONELEVEL)
    [(u'cn=group3,dc=my-domain,dc=com', 
    {u'member': [u'cn=nobody'], 
    u'objectClass': [u'groupOfNames'], 
    u'cn': [u'group3']})]
    
    >>> groups['group1']._member_format
    0
    
    >>> groups['group1']._member_attribute
    'member'

Directly created groups object have no access to it's refering users::

    >>> groups['group1'].member_ids
    Traceback (most recent call last):
      ...
    AttributeError: 'NoneType' object has no attribute 'users'

Create a UGM object::

    >>> from node.ext.ldap.ugm import Ugm
    >>> ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg)

Currently, the member relation is computed hardcoded and maps to object classes.
This will propably change in future. Right now 'posigGroup',
'groupOfUniqueNames', and 'groupOfNames' are supported::

    >>> from node.ext.ldap.ugm._api import member_format, member_attribute
    >>> member_format('groupOfUniqueNames')
    0
    
    >>> member_attribute('groupOfUniqueNames')
    'uniqueMember'
    
    >>> member_format('groupOfNames')
    0
    
    >>> member_attribute('groupOfNames')
    'member'
    
    >>> member_format('posixGroup')
    1
    
    >>> member_attribute('posixGroup')
    'memberUid'
    
    >>> member_format('foo')
    Traceback (most recent call last):
      ...
    Exception: Unknown format
    
    >>> member_attribute('foo')
    Traceback (most recent call last):
      ...
    Exception: Unknown member attribute

Fetch users and groups::

    >>> ugm.users
    <Users object 'users' at ...>
    
    >>> ugm.groups
    <Groups object 'groups' at ...>
    
    >>> ugm.groups['group1'].users
    [<User object 'Schmidt' at ...>, 
    <User object 'M?ller' at ...>]
    
    >>> ugm.users['Schmidt'].groups
    [<Group object 'group1' at ...>]

Test role mappings. Create container for roles.::

    >>> from node.ext.ldap import LDAPNode
    >>> node = LDAPNode('dc=my-domain,dc=com', props)
    >>> node['ou=roles'] = LDAPNode()
    >>> node['ou=roles'].attrs['objectClass'] = ['organizationalUnit']
    >>> node()

Test accessing unconfigured roles.::

    >>> ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg, rcfg=None)
    >>> user = ugm.users['Meier']
    >>> ugm.roles(user)
    []
    
    >>> ugm.add_role('viewer', user)
    Traceback (most recent call last):
      ...
    ValueError: Role support not configured properly
    
    >>> ugm.remove_role('viewer', user)
    Traceback (most recent call last):
      ...
    ValueError: Role support not configured properly

Configure role config represented by object class 'groupOfNames'::

    >>> from node.ext.ldap.ugm import RolesConfig
    >>> rcfg = RolesConfig(
    ...     baseDN='ou=roles,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'cn',
    ...         'rdn': 'cn',
    ...     },
    ...     scope=ONELEVEL,
    ...     queryFilter='(objectClass=groupOfNames)',
    ...     objectClasses=['groupOfNames'],
    ...     defaults={},
    ... )
    
    >>> ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg, rcfg=rcfg)

    >>> roles = ugm._roles
    >>> roles
    <Roles object 'roles' at ...>

No roles yet.::

    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles

Test roles for users.::

    >>> user = ugm.users['Meier']
    >>> ugm.roles(user)
    []

Add role for user, role gets created if not exists.::

    >>> ugm.add_role('viewer', user)
    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles
      <class 'node.ext.ldap.ugm._api.Role'>: viewer
        <class 'node.ext.ldap.ugm._api.User'>: Meier
    
    >>> ugm.roles_storage()

Query roles for principal via ugm object.::

    >>> ugm.roles(user)
    [u'viewer']

Query roles for principal directly.::

    >>> user.roles
    [u'viewer']

Add some roles for 'Schmidt'.::

    >>> user = ugm.users['Schmidt']
    >>> user.add_role('viewer')
    >>> user.add_role('editor')
    
    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles
      <class 'node.ext.ldap.ugm._api.Role'>: viewer
        <class 'node.ext.ldap.ugm._api.User'>: Meier
        <class 'node.ext.ldap.ugm._api.User'>: Schmidt
      <class 'node.ext.ldap.ugm._api.Role'>: editor
        <class 'node.ext.ldap.ugm._api.User'>: Schmidt
    
    >>> user.roles
    [u'viewer', u'editor']
    
    >>> ugm.roles_storage()

Remove role 'viewer'.::

    >>> ugm.remove_role('viewer', user)
    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles
      <class 'node.ext.ldap.ugm._api.Role'>: viewer
        <class 'node.ext.ldap.ugm._api.User'>: Meier
      <class 'node.ext.ldap.ugm._api.Role'>: editor
        <class 'node.ext.ldap.ugm._api.User'>: Schmidt

Remove role 'editor', No other principal left, remove role as well.::

    >>> user.remove_role('editor')
    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles
      <class 'node.ext.ldap.ugm._api.Role'>: viewer
        <class 'node.ext.ldap.ugm._api.User'>: Meier
    
    >>> ugm.roles_storage()

Test roles for group.::

    >>> group = ugm.groups['group1']
    >>> ugm.roles(group)
    []
    
    >>> ugm.add_role('viewer', group)
    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles
      <class 'node.ext.ldap.ugm._api.Role'>: viewer
        <class 'node.ext.ldap.ugm._api.User'>: Meier
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: Schmidt
          <class 'node.ext.ldap.ugm._api.User'>: M?ller
    
    >>> ugm.roles(group)
    [u'viewer']
    
    >>> group.roles
    [u'viewer']
    
    >>> group = ugm.groups['group3']
    >>> group.add_role('viewer')
    >>> group.add_role('editor')
    
    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles
      <class 'node.ext.ldap.ugm._api.Role'>: viewer
        <class 'node.ext.ldap.ugm._api.User'>: Meier
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: Schmidt
          <class 'node.ext.ldap.ugm._api.User'>: M?ller
        <class 'node.ext.ldap.ugm._api.Group'>: group3
      <class 'node.ext.ldap.ugm._api.Role'>: editor
        <class 'node.ext.ldap.ugm._api.Group'>: group3
    
    >>> ugm.roles_storage()
    
If role already granted, an error is raised.::

    >>> group.add_role('editor')
    Traceback (most recent call last):
      ...
    ValueError: Principal already has role 'editor'
    
    >>> group.roles
    [u'viewer', u'editor']
    
    >>> ugm.remove_role('viewer', group)
    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles
      <class 'node.ext.ldap.ugm._api.Role'>: viewer
        <class 'node.ext.ldap.ugm._api.User'>: Meier
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: Schmidt
          <class 'node.ext.ldap.ugm._api.User'>: M?ller
      <class 'node.ext.ldap.ugm._api.Role'>: editor
        <class 'node.ext.ldap.ugm._api.Group'>: group3
    
    >>> group.remove_role('editor')
    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles
      <class 'node.ext.ldap.ugm._api.Role'>: viewer
        <class 'node.ext.ldap.ugm._api.User'>: Meier
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: Schmidt
          <class 'node.ext.ldap.ugm._api.User'>: M?ller
    
    >>> ugm.roles_storage()

If role not exists, an error is raised.::

    >>> group.remove_role('editor')
    Traceback (most recent call last):
      ...
    ValueError: Role not exists 'editor'

If role is not granted, an error is raised.::

    >>> group.remove_role('viewer')
    Traceback (most recent call last):
      ...
    ValueError: Principal does not has role 'viewer'

Roles return ``Role`` instances on ``__getitem__``::

    >>> role = roles['viewer']
    >>> role
    <Role object 'viewer' at ...>

Group keys are prefixed with 'group:'.::

    >>> role.member_ids
    [u'Meier', u'group:group1']

``__getitem__`` of ``Role`` returns ``User`` or ``Group`` instance, depending
on key.::

    >>> role['Meier']
    <User object 'Meier' at ...>
    
    >>> role['group:group1']
    <Group object 'group1' at ...>

A KeyError is raised when trying to access an inexistent role member.::

    >>> role['inexistent']
    Traceback (most recent call last):
      ...
    KeyError: 'inexistent'

A KeyError is raised when trying to delete an inexistent role member.::

    >>> del role['inexistent']
    Traceback (most recent call last):
      ...
    KeyError: 'inexistent'

Delete user and check if roles are removed.::

    >>> ugm.printtree()
    <class 'node.ext.ldap.ugm._api.Ugm'>: None
      <class 'node.ext.ldap.ugm._api.Users'>: users
        <class 'node.ext.ldap.ugm._api.User'>: Meier
        <class 'node.ext.ldap.ugm._api.User'>: M?ller
        <class 'node.ext.ldap.ugm._api.User'>: Schmidt
        <class 'node.ext.ldap.ugm._api.User'>: Umhauer
      <class 'node.ext.ldap.ugm._api.Groups'>: groups
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: Schmidt
          <class 'node.ext.ldap.ugm._api.User'>: M?ller
        <class 'node.ext.ldap.ugm._api.Group'>: group2
          <class 'node.ext.ldap.ugm._api.User'>: Umhauer
        <class 'node.ext.ldap.ugm._api.Group'>: group3
    
    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles
      <class 'node.ext.ldap.ugm._api.Role'>: viewer
        <class 'node.ext.ldap.ugm._api.User'>: Meier
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: Schmidt
          <class 'node.ext.ldap.ugm._api.User'>: M?ller
    
    >>> del ugm.users['Meier']
    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles
      <class 'node.ext.ldap.ugm._api.Role'>: viewer
        <class 'node.ext.ldap.ugm._api.Group'>: group1
          <class 'node.ext.ldap.ugm._api.User'>: Schmidt
          <class 'node.ext.ldap.ugm._api.User'>: M?ller

Delete group and check if roles are removed.::

    >>> del ugm.groups['group1']
    >>> roles.printtree()
    <class 'node.ext.ldap.ugm._api.Roles'>: roles

    >>> ugm.printtree()
    <class 'node.ext.ldap.ugm._api.Ugm'>: None
      <class 'node.ext.ldap.ugm._api.Users'>: users
        <class 'node.ext.ldap.ugm._api.User'>: M?ller
        <class 'node.ext.ldap.ugm._api.User'>: Schmidt
        <class 'node.ext.ldap.ugm._api.User'>: Umhauer
      <class 'node.ext.ldap.ugm._api.Groups'>: groups
        <class 'node.ext.ldap.ugm._api.Group'>: group2
          <class 'node.ext.ldap.ugm._api.User'>: Umhauer
        <class 'node.ext.ldap.ugm._api.Group'>: group3
    
    >>> ugm()
