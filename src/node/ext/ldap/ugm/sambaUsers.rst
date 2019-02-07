Samba users
-----------

::

    >>> from node.ext.ldap.ugm import Ugm

    >>> ucfg = layer['ucfg']
    >>> gcfg = layer['gcfg']
    >>> props = layer['props']

    >>> ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg)
    >>> ugm.users.search()
    ['uid0', 'uid1', 'uid2']

    >>> ugm.users['uid0'].context.attrs['userPassword']
    'secret0'

    >>> ugm.users['uid0'].context.attrs['sambaLMPassword']
    'FF3750BCC2B22412AAD3B435B51404EE'

    >>> ugm.users['uid0'].context.attrs['sambaNTPassword']
    '62CF067F093CD75BBAA5D49E04689ED7'

    >>> ugm.users['uid0'].passwd('secret0', 'newsecret')
    >>> ugm.users['uid0'].context.attrs['userPassword']
    '{SSHA}...'

    >>> ugm.users['uid0'].context.attrs['sambaLMPassword']
    'DB6574A2642D294B9A0F5D12D8F612D0'

    >>> ugm.users['uid0'].context.attrs['sambaNTPassword']
    '58D9F1588236EE9D4ED739E89FFCA25B'
