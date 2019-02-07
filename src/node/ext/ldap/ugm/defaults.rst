Default value callbacks testing
===============================

Test related imports::

    >>> from node.ext.ldap import LDAPNode
    >>> from node.ext.ldap.scope import SUBTREE
    >>> from node.ext.ldap.ugm import Groups
    >>> from node.ext.ldap.ugm import GroupsConfig
    >>> from node.ext.ldap.ugm import Ugm
    >>> from node.ext.ldap.ugm import Users
    >>> from node.ext.ldap.ugm import UsersConfig
    >>> from node.ext.ldap.ugm import defaults
    >>> from node.ext.ldap.ugm import posix
    >>> from node.ext.ldap.ugm import samba
    >>> from node.ext.ldap.ugm import shadow

Test node::

    >>> props = layer['props']
    >>> root = LDAPNode('dc=my-domain,dc=com', props)
    >>> root['ou=defaults'] = LDAPNode()
    >>> root['ou=defaults'].attrs['objectClass'] = ['organizationalUnit']
    >>> root()

Creation defaults::

    >>> sorted(defaults.creation_defaults['posixAccount'].items())
    [('cn', <function cn at ...>), 
    ('gidNumber', <function gidNumber at ...>), 
    ('homeDirectory', <function homeDirectory at ...>), 
    ('uid', <function uid at ...>), 
    ('uidNumber', <function uidNumber at ...>)]

    >>> sorted(defaults.creation_defaults['posixGroup'].items())
    [('cn', <function cn at ...>), 
    ('gidNumber', <function gidNumber at ...>)]

    >>> sorted(defaults.creation_defaults['sambaGroupMapping'].items())
    [('gidNumber', <function gidNumber at ...>), 
    ('sambaGroupType', <function sambaGroupType at ...>), 
    ('sambaSID', <function sambaGroupSID at ...>)] 

    >>> sorted(defaults.creation_defaults['sambaSamAccount'].items())
    [('sambaSID', <function sambaUserSID at ...>)]

    >>> sorted(defaults.creation_defaults['shadowAccount'].items())
    [('uid', <function uid at ...>)]


Posix Account
-------------

::

    >>> ucfg = UsersConfig(
    ...     baseDN='ou=defaults,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'cn',
    ...         'rdn': 'cn',
    ...     },
    ...     scope=SUBTREE,
    ...     queryFilter='(objectClass=posixAccount)',
    ...     objectClasses=['account', 'posixAccount'],
    ...     defaults={},
    ... )
    >>> users = Users(props, ucfg)
    >>> user = users.create('posixuser')
    >>> user()
    >>> sorted(user.context.attrs.items())
    [('cn', 'posixuser'), 
    ('gidNumber', '100'), 
    ('homeDirectory', '/home/posixuser'),
    ('objectClass', ['account', 'posixAccount']), 
    ('uid', 'posixuser'), 
    ('uidNumber', '100')]

    >>> defaults.creation_defaults['posixAccount']['loginShell'] = \
    ...     posix.loginShell

    >>> ucfg = UsersConfig(
    ...     baseDN='ou=defaults,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'uid',
    ...         'rdn': 'uid',
    ...     },
    ...     scope=SUBTREE,
    ...     queryFilter='(objectClass=posixAccount)',
    ...     objectClasses=['account', 'posixAccount'],
    ...     defaults={},
    ... )
    >>> users = Users(props, ucfg)
    >>> user = users.create('posixuser1')
    >>> user()
    >>> sorted(user.context.attrs.items())
    [('cn', 'posixuser1'), 
    ('gidNumber', '101'), 
    ('homeDirectory', '/home/posixuser1'),
    ('loginShell', '/bin/false'), 
    ('objectClass', ['account', 'posixAccount']), 
    ('uid', 'posixuser1'), 
    ('uidNumber', '101')]

    >>> del defaults.creation_defaults['posixAccount']['loginShell']


Posix Group
-----------

::

    >>> gcfg = GroupsConfig(
    ...     baseDN='ou=defaults,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'cn',
    ...         'rdn': 'cn',
    ...     },
    ...     scope=SUBTREE,
    ...     queryFilter='(objectClass=posixGroup)',
    ...     objectClasses=['posixGroup'],
    ...     defaults={},
    ... )
    >>> groups = Groups(props, gcfg)
    >>> group = groups.create('posixgroup')
    >>> group()
    >>> sorted(group.context.attrs.items())
    [('cn', 'posixgroup'), 
    ('gidNumber', '100'),
    ('memberUid', ['nobody']), 
    ('objectClass', ['posixGroup'])]


Shadow Account
--------------

::

    >>> ucfg = UsersConfig(
    ...     baseDN='ou=defaults,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'uid',
    ...         'rdn': 'uid',
    ...     },
    ...     scope=SUBTREE,
    ...     queryFilter='(objectClass=shadowAccount)',
    ...     objectClasses=['account', 'shadowAccount'],
    ...     defaults={},
    ... )
    >>> users = Users(props, ucfg)
    >>> user = users.create('shadowuser')
    >>> user()
    >>> sorted(user.context.attrs.items())
    [('objectClass', ['account', 'shadowAccount']),
    ('uid', 'shadowuser')]

    >>> shadow_d = defaults.creation_defaults['shadowAccount']
    >>> shadow_d['shadowFlag'] = shadow.shadowFlag
    >>> shadow_d['shadowMin'] = shadow.shadowMin
    >>> shadow_d['shadowMax'] = shadow.shadowMax
    >>> shadow_d['shadowWarning'] = shadow.shadowWarning
    >>> shadow_d['shadowInactive'] = shadow.shadowInactive
    >>> shadow_d['shadowLastChange'] = shadow.shadowLastChange
    >>> shadow_d['shadowExpire'] = shadow.shadowExpire

    >>> ucfg = UsersConfig(
    ...     baseDN='ou=defaults,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'uid',
    ...         'rdn': 'uid',
    ...     },
    ...     scope=SUBTREE,
    ...     queryFilter='(objectClass=shadowAccount)',
    ...     objectClasses=['account', 'shadowAccount'],
    ...     defaults={},
    ... )
    >>> users = Users(props, ucfg)
    >>> user = users.create('shadowuser2')
    >>> user()
    >>> sorted(user.context.attrs.items())
    [('objectClass', ['account', 'shadowAccount']), 
    ('shadowExpire', '99999'),
    ('shadowFlag', '0'), 
    ('shadowInactive', '0'), 
    ('shadowLastChange', '12011'), 
    ('shadowMax', '99999'), 
    ('shadowMin', '0'), 
    ('shadowWarning', '0'), 
    ('uid', 'shadowuser2')]

    >>> del shadow_d['shadowFlag']
    >>> del shadow_d['shadowMin']
    >>> del shadow_d['shadowMax']
    >>> del shadow_d['shadowWarning']
    >>> del shadow_d['shadowInactive']
    >>> del shadow_d['shadowLastChange']
    >>> del shadow_d['shadowExpire']


Samba Account
-------------

::

    >>> ucfg = UsersConfig(
    ...     baseDN='ou=defaults,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'cn',
    ...         'rdn': 'cn',
    ...     },
    ...     scope=SUBTREE,
    ...     queryFilter='(objectClass=sambaSamAccount)',
    ...     objectClasses=['account', 'posixAccount', 'sambaSamAccount'],
    ...     defaults={
    ...         'uid': 'sambauser',
    ...     },
    ... )
    >>> users = Users(props, ucfg)
    >>> user = users.create('sambauser')
    >>> user()
    >>> sorted(user.context.attrs.items())
    [('cn', 'sambauser'),
    ('gidNumber', '100'),
    ('homeDirectory', '/home/sambauser'),
    ('objectClass', ['account', 'posixAccount', 'sambaSamAccount']),
    ('sambaSID', 'S-1-5-21-1234567890-1234567890-1234567890-1202'),
    ('uid', 'sambauser'),
    ('uidNumber', '100')]

    >>> user.passwd(None, 'secret')
    >>> sorted(user.context.attrs.items())
    [('cn', 'sambauser'), 
    ('gidNumber', '100'), 
    ('homeDirectory', '/home/sambauser'), 
    ('objectClass', ['account', 'posixAccount', 'sambaSamAccount']), 
    ('sambaLMPassword', '552902031BEDE9EFAAD3B435B51404EE'), 
    ('sambaNTPassword', '878D8014606CDA29677A44EFA1353FC7'), 
    ('sambaSID', 'S-1-5-21-1234567890-1234567890-1234567890-1202'), 
    ('uid', 'sambauser'), 
    ('uidNumber', '100'), 
    ('userPassword', '{SSHA}...')]

    >>> samba_d = defaults.creation_defaults['sambaSamAccount']
    >>> samba_d['sambaDomainName'] = samba.sambaDomainName
    >>> samba_d['sambaPrimaryGroupSID'] = samba.sambaPrimaryGroupSID
    >>> samba_d['sambaAcctFlags'] = samba.sambaAcctFlags

    >>> ucfg = UsersConfig(
    ...     baseDN='ou=defaults,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'cn',
    ...         'rdn': 'cn',
    ...     },
    ...     scope=SUBTREE,
    ...     queryFilter='(objectClass=sambaSamAccount)',
    ...     objectClasses=['account', 'posixAccount', 'sambaSamAccount'],
    ...     defaults={
    ...         'uid': 'sambauser1',
    ...     },
    ... )
    >>> users = Users(props, ucfg)
    >>> user = users.create('sambauser1')
    >>> user()
    >>> sorted(user.context.attrs.items())
    [('cn', 'sambauser1'), 
    ('gidNumber', '101'), 
    ('homeDirectory', '/home/sambauser1'), 
    ('objectClass', ['account', 'posixAccount', 'sambaSamAccount']), 
    ('sambaAcctFlags', '[U]'), 
    ('sambaDomainName', 'CONE_UGM'), 
    ('sambaPrimaryGroupSID', 'S-1-5-21-1234567890-1234567890-1234567890-123'), 
    ('sambaSID', 'S-1-5-21-1234567890-1234567890-1234567890-1202'), 
    ('uid', 'sambauser1'), 
    ('uidNumber', '101')]

    >>> del samba_d['sambaDomainName']
    >>> del samba_d['sambaPrimaryGroupSID']
    >>> del samba_d['sambaAcctFlags']


Samba Group
-----------

::

    >>> gcfg = GroupsConfig(
    ...     baseDN='ou=defaults,dc=my-domain,dc=com',
    ...     attrmap={
    ...         'id': 'cn',
    ...         'rdn': 'cn',
    ...     },
    ...     scope=SUBTREE,
    ...     queryFilter='(objectClass=sambaGroupMapping)',
    ...     objectClasses=['posixGroup', 'sambaGroupMapping'],
    ...     defaults={},
    ... )
    >>> groups = Groups(props, gcfg)
    >>> group = groups.create('sambagroup')
    >>> group()
    >>> sorted(group.context.attrs.items())
    [('cn', 'sambagroup'), 
    ('gidNumber', '100'), 
    ('memberUid', ['nobody']), 
    ('objectClass', ['posixGroup', 'sambaGroupMapping']), 
    ('sambaGroupType', '2'), 
    ('sambaSID', 'S-1-5-21-1234567890-1234567890-1234567890-1202')]
