# -*- coding: utf-8 -*-
from bda.cache.nullcache import NullCacheManager
from ldap import MOD_REPLACE
from node.ext.ldap import LDAPCommunicator
from node.ext.ldap import LDAPConnector
from node.ext.ldap import LDAPProps
from node.ext.ldap import SUBTREE
from node.ext.ldap import testing
from node.ext.ldap.base import cache_key
from node.ext.ldap.base import main
from node.ext.ldap.base import testLDAPConnectivity
from node.tests import NodeTestCase
from zope.component import provideAdapter
import sys


class TestBase(NodeTestCase):
    layer = testing.LDIF_data

    def test_base(self):
        # NullCachManager registration
        provideAdapter(NullCacheManager)

        # Test main script, could be used by command line with
        # 'python base.py server port'::
        old_argv = sys.argv
        sys.argv = ['base.py', '127.0.0.1', '12345']
        self.assertEqual(main(), 'success')

        sys.argv[-1] = '12346'
        self.assertEqual(main().args[0], {
            'result': -1,
            'desc': "Can't contact LDAP server",
            'errno': 107,
            'ctrls': [],
            'info': 'Transport endpoint is not connected'
        })

        sys.argv = []
        self.assertEqual(main(), 'usage: python base.py [server] [port]')

        sys.argv = old_argv

        # Test node.ext.ldap base objects. Test LDAP connectivity
        self.assertEqual(testLDAPConnectivity('127.0.0.1', 12345), 'success')
        self.assertEqual(testLDAPConnectivity('127.0.0.1', 12346).args[0], {
            'result': -1,
            'desc': "Can't contact LDAP server",
            'errno': 107,
            'ctrls': [],
            'info': 'Transport endpoint is not connected'
        })

        # LDAP credentials
        host = "127.0.0.1"
        port = 12345
        binddn = "cn=Manager,dc=my-domain,dc=com"
        bindpw = "secret"

        props = LDAPProps(
            server=host,
            port=port,
            user=binddn,
            password=bindpw
        )

        # Create connector.
        connector = LDAPConnector(props=props)

        # Create communicator.
        communicator = LDAPCommunicator(connector)

        # Bind to directory.
        communicator.bind()

        # Search fails if baseDN is not set and not given to search function
        self.assertEqual(communicator.baseDN, '')

        err = self.expect_error(
            ValueError,
            communicator.search,
            '(objectClass=*)',
            SUBTREE
        )
        self.assertEqual(str(err), 'baseDN unset.')

        # Set base dn and check if previously imported entries are present.
        communicator.baseDN = 'dc=my-domain,dc=com'
        res = communicator.search('(objectClass=*)', SUBTREE)
        self.assertEqual(len(res), 7)

        # Test search pagination
        res, cookie = communicator.search(
            '(objectClass=*)',
            SUBTREE,
            page_size=4,
            cookie=''
        )
        self.assertEqual(len(res), 4)

        res, cookie = communicator.search(
            '(objectClass=*)',
            SUBTREE,
            page_size=4,
            cookie=cookie
        )
        self.assertEqual(len(res), 3)

        self.assertEqual(cookie, b'')

        # Pagination search fails if cookie but no page size given
        res, cookie = communicator.search(
            '(objectClass=*)',
            SUBTREE,
            page_size=4,
            cookie=''
        )
        err = self.expect_error(
            ValueError,
            communicator.search,
            '(objectClass=*)',
            SUBTREE,
            cookie=cookie
        )
        self.assertEqual(str(err), 'cookie passed without page_size')

        # Test inserting entries.
        entry = {
            'cn': b'foo',
            'sn': b'bar',
            'objectclass': (b'person', b'top'),
        }
        dn = 'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com'
        communicator.add(dn, entry)

        # Now there's one more entry in the directory.
        res = communicator.search('(objectClass=*)', SUBTREE)
        self.assertEqual(len(res), 8)

        # Query added entry directly.
        res = communicator.search('(cn=foo)', SUBTREE)
        self.assertEqual(res, [(
            'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com',
            {'objectClass': [b'person', b'top'], 'cn': [b'foo'], 'sn': [b'bar']}
        )])

        # Modify this entry and check the result.
        communicator.modify(res[0][0], [(MOD_REPLACE, 'sn', b'baz')])
        res = communicator.search('(cn=foo)', SUBTREE)
        self.assertEqual(res, [(
            'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com',
            {'objectClass': [b'person', b'top'], 'cn': [b'foo'], 'sn': [b'baz']}
        )])

        # Finally delete this entry and check the result.
        communicator.delete(res[0][0])
        self.assertEqual(communicator.search('(cn=foo)', SUBTREE), [])

        # Unbind from server.
        communicator.unbind()

        # Connector using cache.
        connector = LDAPConnector(props)
        communicator = LDAPCommunicator(connector)
        communicator.bind()

        # Add entry
        entry = {
            'cn': b'foo',
            'sn': b'bar',
            'objectclass': (b'person', b'top'),
        }
        dn = 'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com'
        communicator.add(dn, entry)
        communicator.baseDN = 'dc=my-domain,dc=com'

        # Search cached entry. Does not get cached here since no real cache
        # provider is registered. Thus the nullcacheProviderFactory is used.
        # But cache API is used anyways::
        res = communicator.search('(cn=foo)', SUBTREE)
        self.assertEqual(res, [(
            'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com',
            {'objectClass': [b'person', b'top'], 'cn': [b'foo'], 'sn': [b'bar']}
        )])

        # Delete entry
        communicator.delete(res[0][0])
        res = communicator.search('(cn=foo)', SUBTREE, force_reload=True)
        self.assertEqual(res, [])

        communicator.unbind()

    def test_cache_key(self):
        key = cache_key([
            u'hällo',
            b'w\xc3\xb6rld',
            0,
            None,
            True,
            False,
            [
                u'hällo',
                b'w\xc3\xb6rld',
                0,
                None,
                True,
                False
            ]
        ])
        self.assertEqual(
            key,
            u'hällo-wörld-0-None-True-False-hällo-wörld-0-None-True-False'
        )
