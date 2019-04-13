from ldap.schema.models import AttributeType
from ldap.schema.models import ObjectClass
from ldap.schema.subentry import SubSchema
from node.ext.ldap import LDAPProps
from node.ext.ldap import testing
from node.ext.ldap.schema import LDAPSchemaInfo
from node.tests import NodeTestCase


class TestSchema(NodeTestCase):
    layer = testing.LDIF_data

    def test_schema(self):
        # LDAP credentials.
        host = "127.0.0.1"
        port = 12345
        binddn = "cn=Manager,dc=my-domain,dc=com"
        bindpw = "secret"

        props = LDAPProps(
            server=host,
            port=port,
            user=binddn,
            password=bindpw,
        )

        # Schema object
        info = LDAPSchemaInfo(props)
        self.assertTrue(isinstance(info.subschema, SubSchema))

        # CN Attribute
        attrcn = info.attribute('cn')
        self.assertTrue(isinstance(attrcn, AttributeType))

        self.assertEqual(attrcn.names, ('cn', 'commonName'))
        self.assertFalse(attrcn.collective)
        self.assertEqual(
            attrcn.desc,
            'RFC4519: common name(s) for which the entity is known by'
        )
        self.assertFalse(attrcn.no_user_mod)
        self.assertFalse(attrcn.obsolete)
        self.assertEqual(attrcn.ordering, None)
        self.assertEqual(attrcn.schema_attribute, u'attributeTypes')
        self.assertFalse(attrcn.single_value)
        self.assertEqual(attrcn.substr, None)
        self.assertEqual(attrcn.sup, ('name',))
        self.assertEqual(attrcn.usage, 0)

        gof = info.objectclass('groupOfNames')
        self.assertTrue(isinstance(gof, ObjectClass))
        self.assertEqual(gof.must, ('member', 'cn'))
        self.assertEqual(
            gof.may,
            ('businessCategory', 'seeAlso', 'owner', 'ou', 'o', 'description')
        )

        attrs = info.attributes_of_objectclass('groupOfNames')
        self.assertTrue(isinstance(attrs[0]['info'], AttributeType))
        self.assertEqual(attrs[0]['name'], 'member')
        self.assertEqual(attrs[0]['required'], True)
