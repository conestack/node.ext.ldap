node.ext.ldap.filter
====================

LDAPFilter
----------

LDAPFilter expects string, other LDAPFilter or None at initialization.:: 

    >>> from node.ext.ldap.filter import LDAPFilter
    >>> str(LDAPFilter(None))
    ''
    
    >>> str(LDAPFilter(LDAPFilter(None)))
    ''
    
    >>> str(LDAPFilter(object()))
    Traceback (most recent call last):
      ...
    TypeError: Query filter must be LDAPFilter or string

LDAPFilter can be combined with & and | operators. An operand must be either
another LDAPFilter, a string or a None type.::

    >>> LDAPFilter('(a=*)') & object()
    Traceback (most recent call last):
      ...
    TypeError: unsupported operand type
    
    >>> LDAPFilter('(a=*)') | object()
    Traceback (most recent call last):
      ...
    TypeError: unsupported operand type
    
    >>> foo = LDAPFilter('(a=*)') & None
    >>> foo
    LDAPFilter('(a=*)')
    
    >>> foo = LDAPFilter('(a=*)') | None
    >>> foo
    LDAPFilter('(a=*)')
    
    >>> filter = LDAPFilter('(objectClass=person)')
    >>> filter |= LDAPFilter('(objectClass=some)')
    >>> filter
    LDAPFilter('(|(objectClass=person)(objectClass=some))')
    
    >>> str(filter)
    '(|(objectClass=person)(objectClass=some))'
    
    >>> filter &= LDAPFilter('(objectClass=other)')
    >>> str(filter)
    '(&(|(objectClass=person)(objectClass=some))(objectClass=other))'


LDAPDictFilter
--------------

LDAPDictFilter inherits from LDAPFilter and provides converting dict like
objects to LDAP filters.::

    >>> from node.ext.ldap.filter import dict_to_filter
    >>> str(dict_to_filter(dict(), False))
    ''
    
    >>> from node.ext.ldap.filter import LDAPDictFilter
    >>> criteria = dict(sn='meier', cn='sepp')
    >>> filter = LDAPDictFilter(criteria, or_search=True)
    >>> filter
    LDAPDictFilter(criteria={'cn': 'sepp', 'sn': 'meier'})
    
    >>> str(filter)
    '(|(cn=sepp)(sn=meier))'
    
    >>> criteria = dict(mail='*@example.com', homeDirectory='/home/*')
    >>> other_filter = LDAPDictFilter(criteria)
    >>> str(other_filter)
    '(&(mail=*@example.com)(homeDirectory=/home/*))'
    
    >>> str(filter & other_filter)
    '(&(|(cn=sepp)(sn=meier))(&(mail=*@example.com)(homeDirectory=/home/*)))'
    
    >>> str(filter | other_filter)
    '(|(|(cn=sepp)(sn=meier))(&(mail=*@example.com)(homeDirectory=/home/*)))'
    
    >>> str(filter & LDAPFilter('(objectClass=person)'))
    '(&(|(cn=sepp)(sn=meier))(objectClass=person))'


LDAPRelationFilter
------------------

LDAPRelationFilter inherits from LDAPFilter and provides creating LDAP filters
from relations.::

    >>> from node.base import AttributedNode
    >>> node = AttributedNode()
    >>> node.attrs['someUid'] = '123'
    >>> node.attrs['someName'] = 'Name'
    
    >>> from node.ext.ldap.filter import LDAPRelationFilter
    >>> rel_filter = LDAPRelationFilter(node, 'someUid:otherUid')
    >>> rel_filter
    LDAPRelationFilter('(otherUid=123)')
    
    >>> str(rel_filter)
    '(otherUid=123)'
    
    >>> rel_filter = LDAPRelationFilter(
    ...     node, 'someUid:otherUid|someName:otherName')
    >>> str(rel_filter)
    '(|(otherUid=123)(otherName=Name))'
    
    >>> rel_filter &= LDAPFilter('(objectClass=person)')
    >>> str(rel_filter)
    '(&(|(otherUid=123)(otherName=Name))(objectClass=person))'
    
    >>> rel_filter = LDAPRelationFilter(
    ...     node, 'someUid:otherUid|someName:otherName', False)
    >>> str(rel_filter)
    '(&(otherUid=123)(otherName=Name))'
    
    >>> rel_filter = LDAPRelationFilter(
    ...     node, 'someUid:otherUid|someUid:otherName', False)
    >>> str(rel_filter)
    '(&(otherUid=123)(otherName=123))'
    
    >>> rel_filter = LDAPRelationFilter(
    ...     node, 'someUid:otherUid|inexistent:inexistent')
    >>> str(rel_filter)
    '(otherUid=123)'
