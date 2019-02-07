Test related imports::

    >>> from node.ext.ldap import LDAPProps
    >>> from node.ext.ldap.schema import LDAPSchemaInfo

LDAP credentials.::

    >>> host = "127.0.0.1"
    >>> port = 12345
    >>> binddn = "cn=Manager,dc=my-domain,dc=com"
    >>> bindpw = "secret"

    >>> props = LDAPProps(
    ...     server=host,
    ...     port=port,
    ...     user=binddn,
    ...     password=bindpw,
    ... )

Schema object::

    >>> info = LDAPSchemaInfo(props)
    >>> info.subschema
    <ldap.schema.subentry.SubSchema ...>

CN Attribute::

    >>> attrcn = info.attribute('cn')
    >>> attrcn
    <ldap.schema.models.AttributeType ...>

    >>> attrcn.names[0] == 'cn'
    True

    >>> attrcn.names[1] == 'commonName'
    True

    >>> attrcn.collective
    False

    >>> attrcn.desc
    'RFC4519: common name(s) for which the entity is known by'

    >>> attrcn.no_user_mod
    False

    >>> attrcn.obsolete
    False

    >>> attrcn.ordering

    >>> attrcn.schema_attribute
    'attributeTypes'

    >>> attrcn.single_value
    False

    >>> attrcn.substr

    >>> attrcn.sup
    ('name',)

    >>> attrcn.usage
    0

    >>> gof = info.objectclass('groupOfNames')
    >>> gof
    <ldap.schema.models.ObjectClass ...>

    >>> gof.must
    ('member', 'cn')

    >>> gof.may
    ('businessCategory', 'seeAlso', 'owner', 'ou', 'o', 'description')

    >>> pprint(info.attributes_of_objectclass('groupOfNames'))
    [{'info': <ldap.schema.models.AttributeType ...>,
      'name': 'member',
      'required': True},
     {'info': <ldap.schema.models.AttributeType ...>,
      'name': 'cn',
      'required': True},
     {'info': <ldap.schema.models.AttributeType ...>,
      'name': 'businessCategory',
      'required': False},
     {'info': <ldap.schema.models.AttributeType ...>,
      'name': 'seeAlso',
      'required': False},
     {'info': <ldap.schema.models.AttributeType ...>,
      'name': 'owner',
      'required': False},
     {'info': <ldap.schema.models.AttributeType ...>,
      'name': 'ou',
      'required': False},
     {'info': <ldap.schema.models.AttributeType ...>,
      'name': 'o',
      'required': False},
     {'info': <ldap.schema.models.AttributeType ...>,
      'name': 'description',
      'required': False}]
      
