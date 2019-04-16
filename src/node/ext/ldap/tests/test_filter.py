# -*- coding: utf-8 -*-
from node.base import AttributedNode
from node.ext.ldap import testing
from node.ext.ldap.filter import dict_to_filter
from node.ext.ldap.filter import LDAPDictFilter
from node.ext.ldap.filter import LDAPFilter
from node.ext.ldap.filter import LDAPRelationFilter
from node.tests import NodeTestCase
from odict import odict


class TestFilter(NodeTestCase):
    layer = testing.LDIF_data

    def test_LDAPFilter(self):
        # LDAPFilter expects string, other LDAPFilter or None at
        # initialization.
        self.assertEqual(str(LDAPFilter(None)), '')
        self.assertEqual(str(LDAPFilter(LDAPFilter(None))), '')

        err = self.expect_error(
            TypeError,
            lambda: str(LDAPFilter(object()))
        )
        self.assertEqual(str(err), 'Query filter must be LDAPFilter or string')

        # LDAPFilter can be combined with & and | operators. An operand must be
        # either another LDAPFilter, a string or a None type.
        err = self.expect_error(
            TypeError,
            lambda: LDAPFilter('(a=*)') & object()
        )
        self.assertEqual(str(err), 'unsupported operand type')

        err = self.expect_error(
            TypeError,
            lambda: LDAPFilter('(a=*)') | object()
        )
        self.assertEqual(str(err), 'unsupported operand type')

        foo = LDAPFilter('(a=*)') & None
        self.assertEqual(str(foo), '(a=*)')
        self.assertEqual(str(foo), str(LDAPFilter('(a=*)')))

        foo = LDAPFilter('(a=*)') | None
        self.assertEqual(str(foo), '(a=*)')
        self.assertEqual(str(foo), str(LDAPFilter('(a=*)')))

        foo = LDAPFilter('(a=ä)')
        self.assertEqual(str(foo), '(a=ä)')
        self.assertEqual(str(foo), str(LDAPFilter(u'(a=ä)')))

        self.assertTrue('a' in foo)
        self.assertFalse('objectClass' in foo)

        filter = LDAPFilter('(objectClass=person)')
        filter |= LDAPFilter('(objectClass=some)')
        self.assertEqual(
            str(filter),
            '(|(objectClass=person)(objectClass=some))'
        )

        filter &= LDAPFilter('(objectClass=other)')
        self.assertEqual(
            str(filter),
            '(&(|(objectClass=person)(objectClass=some))(objectClass=other))'
        )

        filter = LDAPFilter('(objectClass=personä)')
        filter |= LDAPFilter('(objectClass=someä)')
        self.assertEqual(
            str(filter),
            '(|(objectClass=personä)(objectClass=someä))'
        )

        self.assertTrue('objectClass' in filter)
        self.assertEqual(
            repr(filter),
            "LDAPFilter('(|(objectClass=personä)(objectClass=someä))')"
        )

    def test_LDAPDictFilter(self):
        # LDAPDictFilter inherits from LDAPFilter and provides converting dict
        # like objects to LDAP filters.
        self.assertEqual(str(dict_to_filter(dict(), False)), '')

        criteria = dict(sn='meierä', cn='sepp')
        filter = LDAPDictFilter(criteria, or_search=True)
        self.assertEqual(
            repr(filter),
            "LDAPDictFilter(criteria={'cn': 'sepp', 'sn': 'meierä'})"
        )
        self.assertEqual(str(filter), '(|(cn=sepp)(sn=meierä))')

        criteria = dict(mail='*@example.com', homeDirectory='/home/*')
        other_filter = LDAPDictFilter(criteria)
        self.assertEqual(
            str(other_filter),
            '(&(homeDirectory=\\2fhome\\2f*)(mail=*@example.com))'
        )
        self.assertEqual(
            str(filter & other_filter),
            '(&(|(cn=sepp)(sn=meierä))(&(homeDirectory=\\2fhome\\2f*)(mail=*@example.com)))'
        )
        self.assertEqual(
            str(filter | other_filter),
            '(|(|(cn=sepp)(sn=meierä))(&(homeDirectory=\\2fhome\\2f*)(mail=*@example.com)))'
        )
        self.assertEqual(
            str(filter & LDAPFilter('(objectClass=person)')),
            '(&(|(cn=sepp)(sn=meierä))(objectClass=person))'
        )

        # fine-grained control with or_keys and or_values
        criteria = odict((('a', [1, 2]), ('b', [3, 4]), ('c', 5)))
        self.assertEqual(
            str(LDAPDictFilter(criteria)),
            '(&(&(&(a=1)(a=2))(&(b=3)(b=4)))(c=5))'
        )
        self.assertEqual(
            str(LDAPDictFilter(criteria, or_keys=True)),
            '(|(|(&(a=1)(a=2))(&(b=3)(b=4)))(c=5))'
        )
        self.assertEqual(
            str(LDAPDictFilter(criteria, or_values=True)),
            '(&(&(|(a=1)(a=2))(|(b=3)(b=4)))(c=5))'
        )
        self.assertEqual(
            str(LDAPDictFilter(criteria, or_search=True)),
            '(|(|(|(a=1)(a=2))(|(b=3)(b=4)))(c=5))'
        )
        self.assertEqual(
            str(LDAPDictFilter(criteria, or_search=True, or_keys=False)),
            '(&(&(|(a=1)(a=2))(|(b=3)(b=4)))(c=5))'
        )
        self.assertEqual(
            str(LDAPDictFilter(criteria, or_search=True, or_values=False)),
            '(|(|(&(a=1)(a=2))(&(b=3)(b=4)))(c=5))'
        )

    def test_LDAPRelationFilter(self):
        # LDAPRelationFilter inherits from LDAPFilter and provides creating
        # LDAP filters from relations.
        node = AttributedNode()
        node.attrs['someUid'] = '123ä'
        node.attrs['someName'] = 'Name'

        rel_filter = LDAPRelationFilter(node, '')
        self.assertEqual(str(rel_filter), '')

        rel_filter = LDAPRelationFilter(node, 'someUid:otherUid')
        rel_filter

        self.assertEqual(str(rel_filter), '(otherUid=123ä)')

        rel_filter = LDAPRelationFilter(
            node,
            'someUid:otherUid|someName:otherName'
        )
        self.assertEqual(
            str(rel_filter),
            '(|(otherName=Name)(otherUid=123ä))'
        )

        rel_filter &= LDAPFilter('(objectClass=person)')
        self.assertEqual(
            str(rel_filter),
            '(&(|(otherName=Name)(otherUid=123ä))(objectClass=person))'
        )

        rel_filter = LDAPRelationFilter(
            node,
            'someUid:otherUid|someName:otherName',
            False
        )
        self.assertEqual(
            str(rel_filter),
            '(&(otherName=Name)(otherUid=123ä))'
        )

        rel_filter = LDAPRelationFilter(
            node,
            'someUid:otherUid|someUid:otherName',
            False
        )
        self.assertEqual(
            str(rel_filter),
            '(&(otherName=123ä)(otherUid=123ä))'
        )

        rel_filter = LDAPRelationFilter(
            node,
            'someUid:otherUid|inexistent:inexistent'
        )
        self.assertEqual(str(rel_filter), '(otherUid=123ä)')
