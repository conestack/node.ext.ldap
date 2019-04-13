from node.ext.ldap import LDAPProps
from node.ext.ldap import testing
from node.ext.ldap.properties import BINARY_DEFAULTS
from node.ext.ldap.properties import MULTIVALUED_DEFAULTS
from node.tests import NodeTestCase


class TestProperties(NodeTestCase):
    layer = testing.LDIF_data

    def test_LDAPProps(self):
        # Defaults
        self.assertEqual(MULTIVALUED_DEFAULTS, set([
            'member',
            'memberUid',
            'uniqueMember',
            'memberOf'
        ]))

        self.assertEqual(BINARY_DEFAULTS, set([
            'authorityRevocationList',
            'certificateRevocationList',
            'supportedAlgorithms',
            'photo',
            'deltaRevocationList',
            'cACertificate',
            'userCertificate',
            'userPKCS12',
            'crossCertificatePair',
            'objectSid',
            'userSMIMECertificate',
            'jpegPhoto',
            'objectGUID'
        ]))

        # Test LDAPProps
        props = LDAPProps(
            uri='ldap://localhost:12345/',
            user='admin',
            password='secret',
        )
        self.assertEqual(props.uri, 'ldap://localhost:12345/')
        self.assertEqual(props.user, 'admin')
        self.assertEqual(props.password, 'secret')
        self.assertEqual(props.cache, True)
        self.assertEqual(props.timeout, 43200)
        self.assertEqual(props.start_tls, 0)
        self.assertEqual(props.ignore_cert, 0)
        self.assertEqual(props.tls_cacertfile, None)
        self.assertEqual(props.retry_max, 1)
        self.assertEqual(props.retry_delay, 10.)
        self.assertEqual(props.multivalued_attributes, MULTIVALUED_DEFAULTS)
        self.assertEqual(props.binary_attributes, BINARY_DEFAULTS)
        self.assertEqual(props.page_size, 1000)
