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

    >>> defaults.creation_defaults
    {'shadowAccount': 
    {'uid': <function uid at ...>}, 
    'posixGroup': 
    {'gidNumber': <function gidNumber at ...>, 
    'cn': <function cn at ...>}, 
    'sambaGroupMapping': 
    {'sambaGroupType': <function sambaGroupType at ...>, 
    'gidNumber': <function gidNumber at ...>, 
    'sambaSID': <function sambaGroupSID at ...>}, 
    'posixAccount': 
    {'gidNumber': <function gidNumber at ...>, 
    'homeDirectory': <function homeDirectory at ...>, 
    'uidNumber': <function uidNumber at ...>, 
    'cn': <function cn at ...>, 
    'uid': <function uid at ...>}, 
    'sambaSamAccount': 
    {'sambaSID': <function sambaUserSID at ...>}}


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
    >>> user.context.attrs.items()
    [(u'cn', u'posixuser'), 
    (u'uid', u'posixuser'), 
    (u'objectClass', [u'account', u'posixAccount']), 
    (u'uidNumber', u'100'), 
    (u'gidNumber', u'100'), 
    (u'homeDirectory', u'/home/posixuser')]

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
    >>> user.context.attrs.items()
    [(u'uid', u'posixuser1'), 
    (u'cn', u'posixuser1'), 
    (u'objectClass', [u'account', u'posixAccount']), 
    (u'loginShell', u'/bin/false'), 
    (u'uidNumber', u'101'), 
    (u'gidNumber', u'101'), 
    (u'homeDirectory', u'/home/posixuser1')]

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
    >>> group.context.attrs.items()
    [(u'cn', u'posixgroup'), 
    (u'memberUid', ['nobody']), 
    (u'objectClass', [u'posixGroup']), 
    (u'gidNumber', u'100')]


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
    >>> user.context.attrs.items()
    [(u'uid', u'shadowuser'), 
    (u'objectClass', [u'account', u'shadowAccount'])]

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
    >>> user.context.attrs.items()
    [(u'uid', u'shadowuser2'), 
    (u'shadowFlag', u'0'), 
    (u'shadowMin', u'0'), 
    (u'shadowWarning', u'0'), 
    (u'objectClass', [u'account', u'shadowAccount']), 
    (u'shadowInactive', u'0'), 
    (u'shadowMax', u'99999'), 
    (u'shadowLastChange', u'12011'), 
    (u'shadowExpire', u'99999')]

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
    [(u'cn', u'sambauser'),
    (u'gidNumber', u'100'),
    (u'homeDirectory', u'/home/sambauser'),
    (u'objectClass', [u'account', u'posixAccount', u'sambaSamAccount']),
    (u'sambaSID', u'S-1-5-21-1234567890-1234567890-1234567890-1202'),
    (u'uid', u'sambauser'),
    (u'uidNumber', u'100')]

    >>> user.passwd(None, 'secret')
    >>> sorted(user.context.attrs.items())
    [(u'cn', u'sambauser'), 
    (u'gidNumber', u'100'), 
    (u'homeDirectory', u'/home/sambauser'), 
    (u'objectClass', [u'account', u'posixAccount', u'sambaSamAccount']), 
    (u'sambaLMPassword', u'552902031BEDE9EFAAD3B435B51404EE'), 
    (u'sambaNTPassword', u'878D8014606CDA29677A44EFA1353FC7'), 
    (u'sambaSID', u'S-1-5-21-1234567890-1234567890-1234567890-1202'), 
    (u'uid', u'sambauser'), 
    (u'uidNumber', u'100'), 
    (u'userPassword', u'{SSHA}...')]

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
    [(u'cn', u'sambauser1'), 
    (u'gidNumber', u'101'), 
    (u'homeDirectory', u'/home/sambauser1'), 
    (u'objectClass', [u'account', u'posixAccount', u'sambaSamAccount']), 
    (u'sambaAcctFlags', u'[U]'), 
    (u'sambaDomainName', u'CONE_UGM'), 
    (u'sambaPrimaryGroupSID', u'S-1-5-21-1234567890-1234567890-1234567890-123'), 
    (u'sambaSID', u'S-1-5-21-1234567890-1234567890-1234567890-1202'), 
    (u'uid', u'sambauser1'), 
    (u'uidNumber', u'101')]

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
    [(u'cn', u'sambagroup'), 
    (u'gidNumber', u'100'), 
    (u'memberUid', ['nobody']), 
    (u'objectClass', [u'posixGroup', u'sambaGroupMapping']), 
    (u'sambaGroupType', u'2'), 
    (u'sambaSID', u'S-1-5-21-1234567890-1234567890-1234567890-1202')]
