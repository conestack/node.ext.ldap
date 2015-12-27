node.ext.ldap.filter
====================

Test related imports::

    >>> from node.base import AttributedNode
    >>> from node.ext.ldap.filter import LDAPDictFilter
    >>> from node.ext.ldap.filter import LDAPFilter
    >>> from node.ext.ldap.filter import LDAPRelationFilter
    >>> from node.ext.ldap.filter import dict_to_filter
    >>> from odict import odict


LDAPFilter
----------

LDAPFilter expects string, other LDAPFilter or None at initialization.:: 

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

    >>> foo = LDAPFilter(u'(a=\xe4)')
    >>> foo
    LDAPFilter('(a=ä)')

    >>> filter = LDAPFilter('(objectClass=person)')
    >>> filter |= LDAPFilter('(objectClass=some)')
    >>> filter
    LDAPFilter('(|(objectClass=person)(objectClass=some))')

    >>> str(filter)
    '(|(objectClass=person)(objectClass=some))'

    >>> filter &= LDAPFilter('(objectClass=other)')
    >>> str(filter)
    '(&(|(objectClass=person)(objectClass=some))(objectClass=other))'

    >>> filter = LDAPFilter(u'(objectClass=person\xe4)')
    >>> filter |= LDAPFilter(u'(objectClass=some\xe4)')
    >>> filter
    LDAPFilter('(|(objectClass=personä)(objectClass=someä))')


LDAPDictFilter
--------------

LDAPDictFilter inherits from LDAPFilter and provides converting dict like
objects to LDAP filters.::

    >>> str(dict_to_filter(dict(), False))
    ''

    >>> criteria = dict(sn=u'meier\xe4', cn='sepp')
    >>> filter = LDAPDictFilter(criteria, or_search=True)
    >>> filter
    LDAPDictFilter(criteria={'cn': 'sepp', 'sn': u'meier\xe4'})

    >>> str(filter)
    '(|(cn=sepp)(sn=meier\xc3\xa4))'

    >>> criteria = dict(mail='*@example.com', homeDirectory='/home/*')
    >>> other_filter = LDAPDictFilter(criteria)
    >>> str(other_filter)
    '(&(mail=*@example.com)(homeDirectory=\\2fhome\\2f*))'

    >>> str(filter & other_filter)
    '(&(|(cn=sepp)(sn=meier\xc3\xa4))(&(mail=*@example.com)(homeDirectory=\\2fhome\\2f*)))'

    >>> str(filter | other_filter)
    '(|(|(cn=sepp)(sn=meier\xc3\xa4))(&(mail=*@example.com)(homeDirectory=\\2fhome\\2f*)))'

    >>> str(filter & LDAPFilter('(objectClass=person)'))
    '(&(|(cn=sepp)(sn=meier\xc3\xa4))(objectClass=person))'

fine-grained control with or_keys and or_values::

    >>> criteria = odict((('a', [1, 2]), ('b', [3, 4]), ('c', 5)))
    >>> str(LDAPDictFilter(criteria))
    '(&(&(&(a=1)(a=2))(&(b=3)(b=4)))(c=5))'

    >>> str(LDAPDictFilter(criteria, or_keys=True))
    '(|(|(&(a=1)(a=2))(&(b=3)(b=4)))(c=5))'

    >>> str(LDAPDictFilter(criteria, or_values=True))
    '(&(&(|(a=1)(a=2))(|(b=3)(b=4)))(c=5))'

    >>> str(LDAPDictFilter(criteria, or_search=True))
    '(|(|(|(a=1)(a=2))(|(b=3)(b=4)))(c=5))'

    >>> str(LDAPDictFilter(criteria, or_search=True, or_keys=False))
    '(&(&(|(a=1)(a=2))(|(b=3)(b=4)))(c=5))'

    >>> str(LDAPDictFilter(criteria, or_search=True, or_values=False))
    '(|(|(&(a=1)(a=2))(&(b=3)(b=4)))(c=5))'


LDAPRelationFilter
------------------

LDAPRelationFilter inherits from LDAPFilter and provides creating LDAP filters
from relations.::

    >>> node = AttributedNode()
    >>> node.attrs['someUid'] = u'123\xe4'
    >>> node.attrs['someName'] = 'Name'

    >>> rel_filter = LDAPRelationFilter(node, 'someUid:otherUid')
    >>> rel_filter
    LDAPRelationFilter('(otherUid=123ä)')

    >>> str(rel_filter)
    '(otherUid=123\xc3\xa4)'

    >>> rel_filter = LDAPRelationFilter(
    ...     node, 'someUid:otherUid|someName:otherName')
    >>> str(rel_filter)
    '(|(otherUid=123\xc3\xa4)(otherName=Name))'

    >>> rel_filter &= LDAPFilter('(objectClass=person)')
    >>> str(rel_filter)
    '(&(|(otherUid=123\xc3\xa4)(otherName=Name))(objectClass=person))'

    >>> rel_filter = LDAPRelationFilter(
    ...     node, 'someUid:otherUid|someName:otherName', False)
    >>> str(rel_filter)
    '(&(otherUid=123\xc3\xa4)(otherName=Name))'

    >>> rel_filter = LDAPRelationFilter(
    ...     node, 'someUid:otherUid|someUid:otherName', False)
    >>> str(rel_filter)
    '(&(otherUid=123\xc3\xa4)(otherName=123\xc3\xa4))'

    >>> rel_filter = LDAPRelationFilter(
    ...     node, 'someUid:otherUid|inexistent:inexistent')
    >>> str(rel_filter)
    '(otherUid=123\xc3\xa4)'
