from ldap import MOD_REPLACE
from node.ext.ldap import LDAPProps
from node.ext.ldap import LDAPSession
from node.ext.ldap import SUBTREE
from node.ext.ldap import testing
from node.ext.ldap.testing import props
from node.tests import NodeTestCase


class TestSession(NodeTestCase):
    layer = testing.LDIF_data

    def test_session(self):
        # Create the session with ``LDAPProps`` as argument
        session = LDAPSession(props)
        self.assertEqual(session.checkServerProperties(), (True, 'OK'))

        # There's no search base DN set yet
        self.assertEqual(session.baseDN, '')

        # Set a baseDN and perform LDAP search
        session.baseDN = 'dc=my-domain,dc=com'
        res = session.search('(objectClass=*)', SUBTREE)
        self.assertEqual(len(res), 7)

        # Perform batched search
        session.baseDN = 'dc=my-domain,dc=com'
        res, cookie = session.search('(objectClass=*)', SUBTREE, page_size=2)
        self.assertTrue(len(cookie) > 0)
        self.assertEqual(len(res), 2)

        res, cookie = session.search('(objectClass=*)', SUBTREE, page_size=2, cookie=cookie)
        self.assertTrue(len(cookie) > 0)
        self.assertEqual(len(res), 2)

        res, cookie = session.search('(objectClass=*)', SUBTREE, page_size=3, cookie=cookie)
        self.assertTrue(len(cookie) == 0)
        self.assertEqual(len(res), 3)

        res, cookie = session.search('(objectClass=*)', SUBTREE, page_size=2, cookie=cookie)
        self.assertEqual(len(res), 2)

        res, cookie = session.search('(objectClass=*)', SUBTREE, page_size=2, cookie=cookie)
        self.assertEqual(len(res), 2)

        # Add an entry
        entry = {
            'cn': b'foo',
            'sn': b'bar',
            'objectclass': (b'person', b'top'),
        }
        dn = 'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com'
        session.add(dn, entry)
        res = session.search('(objectClass=*)', SUBTREE)
        self.assertEqual(len(res), 8)

        # Modify this entry and check the result
        res = session.search('(cn=foo)', SUBTREE)
        self.assertEqual(res, [(
            'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com',
            {'objectClass': [b'person', b'top'], 'cn': [b'foo'], 'sn': [b'bar']}
        )])

        session.modify(res[0][0], [(MOD_REPLACE, 'sn', b'baz')])
        res = session.search('(cn=foo)', SUBTREE)
        self.assertEqual(res, [(
            'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com',
            {'objectClass': [b'person', b'top'], 'cn': [b'foo'], 'sn': [b'baz']}
        )])

        # Query only specific attributes
        res = session.search('(cn=foo)', SUBTREE, attrlist=('sn',))
        self.assertEqual(res, [(
            'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com',
            {'sn': [b'baz']}
        )])

        # And only the attributes without the values
        res = session.search('(cn=foo)', SUBTREE, attrlist=('sn',), attrsonly=True)
        self.assertEqual(res, [(
            'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com',
            {'sn': []}
        )])

        # Delete this entry and check the result
        session.delete(res[0][0])
        self.assertEqual(session.search('(cn=foo)', SUBTREE), [])

        # Unbind from Server
        session.unbind()

        # Create the session with invalid ``LDAPProps``
        session = LDAPSession(LDAPProps())
        res = session.checkServerProperties()
        self.assertEqual(res[0], False)
        self.assertEqual(res[1].args[0], {
            'result': -1,
            'desc': "Can't contact LDAP server",
            'errno': 107,
            'ctrls': [],
            'info': 'Transport endpoint is not connected'
        })
