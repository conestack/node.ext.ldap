LDAP credentials.::

    >>> host = "127.0.0.1"
    >>> port = 12345
    >>> binddn = "cn=Manager,dc=my-domain,dc=com"
    >>> bindpw = "secret"
    
    >>> from node.ext.ldap import LDAPProps
    >>> props = LDAPProps(
    ...     server=host,
    ...     port=port,
    ...     user=binddn,
    ...     password=bindpw,
    ... )

Schema object::
  
    >>> from node.ext.ldap.schema import LDAPSchemaInfo 
    >>> info = LDAPSchemaInfo(props)
    >>> info.subschema
    <ldap.schema.subentry.SubSchema instance at 0x...>
    
    >>> attrcn = info.attribute('cn')
    >>> attrcn
    <ldap.schema.models.AttributeType instance at 0x...>
    
    >>> attrcn.names
    ('cn', 'commonName')    
    
    >>> gof = info.objectclass('groupOfNames')
    >>> gof
    <ldap.schema.models.ObjectClass instance at 0x...>
    
    >>> gof.must
    ('member', 'cn')
    
    >>> gof.may
    ('businessCategory', 'seeAlso', 'owner', 'ou', 'o', 'description')