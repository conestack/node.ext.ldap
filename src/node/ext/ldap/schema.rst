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
    
    >>> info['cn']
    <ldap.schema.models.AttributeType instance at 0x...>