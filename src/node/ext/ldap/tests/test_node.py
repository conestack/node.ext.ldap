# -*- coding: utf-8 -*-
from node.base import AttributedNode
from node.base import BaseNode
from node.ext.ldap import LDAPNode
from node.ext.ldap import LDAPNodeAttributes
from node.ext.ldap import testing
from node.ext.ldap._node import ACTION_ADD
from node.ext.ldap._node import ACTION_MODIFY
from node.ext.ldap.events import LDAPNodeAddedEvent
from node.ext.ldap.filter import LDAPFilter
from node.ext.ldap.filter import LDAPRelationFilter
from node.ext.ldap.interfaces import ILDAPNodeAddedEvent
from node.ext.ldap.interfaces import ILDAPNodeCreatedEvent
from node.ext.ldap.interfaces import ILDAPNodeDetachedEvent
from node.ext.ldap.interfaces import ILDAPNodeModifiedEvent
from node.ext.ldap.interfaces import ILDAPNodeRemovedEvent
from node.ext.ldap.schema import LDAPSchemaInfo
from node.ext.ldap.scope import ONELEVEL
from node.ext.ldap.scope import SUBTREE
from node.ext.ldap.session import LDAPSession
from node.ext.ldap.testing import props
from node.interfaces import INode
from node.tests import NodeTestCase
from odict import odict
from plone.testing.zca import popGlobalRegistry
from plone.testing.zca import pushGlobalRegistry
from zope.component import adapter
from zope.component import provideHandler
from zope.component.event import objectEventNotify
import ldap
import os


class TestNode(NodeTestCase):
    layer = testing.LDIF_data

    def test_basics(self):
        # Create the root node. The Root node expects the initial base DN as
        # name and the server properties
        err = self.expect_error(
            ValueError,
            LDAPNode,
            'dc=my-domain,dc=com'
        )
        self.assertEqual(str(err), 'Wrong initialization.')

        err = self.expect_error(
            ValueError,
            LDAPNode,
            props=props
        )
        self.assertEqual(str(err), 'Wrong initialization.')

        # DN gets automatically converted to text if necessary
        root = LDAPNode(b'dc=my-domain,dc=com', props)
        self.assertEqual(repr(root), '<dc=my-domain,dc=com - False>')

        # The non-unicode name got decoded
        self.assertEqual(root.name, u'dc=my-domain,dc=com')
        self.assertEqual(root.rdn_attr, 'dc')

        # Check exists
        self.assertTrue(root.exists)

        inexistent = LDAPNode('dc=other-domain,dc=com', props)
        self.assertFalse(inexistent.exists)

        # LDAP attributes for DN are stored on ``attrs``
        self.assertTrue(isinstance(root.attrs, LDAPNodeAttributes))

        # The node has session
        self.assertTrue(isinstance(root.ldap_session, LDAPSession))

        # Check and modify attributes of root
        self.assertEqual(sorted(root.attrs.items()), [
            ('dc', 'my-domain'),
            ('o', 'my-organization'),
            ('objectClass', ['top', 'dcObject', 'organization'])
        ])

        root.attrs['o'] = 'foo'

        # On ``__call__`` data gets persisted
        root()
        self.assertEqual(sorted(root.attrs.items()), [
            ('dc', 'my-domain'),
            ('o', 'foo'),
            ('objectClass', ['top', 'dcObject', 'organization'])
        ])

        # Recreate root and check changed attributes
        root = LDAPNode('dc=my-domain,dc=com', props)
        self.assertEqual(sorted(root.attrs.items()), [
            ('dc', 'my-domain'),
            ('o', 'foo'),
            ('objectClass', ['top', 'dcObject', 'organization'])
        ])

        # Reset o
        root.attrs['o'] = 'my-organization'
        root()

        # Check child keys of root
        self.assertEqual(root.keys(), ['ou=customers', 'ou=demo'])

        # Access inexistent child
        self.expect_error(KeyError, root.__getitem__, 'foo')

    def test_child_basics(self):
        # Access existent child and it's attributes
        root = LDAPNode('dc=my-domain,dc=com', props)
        customers = root['ou=customers']
        self.assertEqual(
            repr(customers),
            '<ou=customers,dc=my-domain,dc=com:ou=customers - False>'
        )

        self.assertEqual(sorted(customers.attrs.items()), [
            ('businessCategory', 'customers_container'),
            ('description', 'customers'),
            ('objectClass', ['top', 'organizationalUnit']),
            ('ou', 'customers')
        ])

        self.assertEqual(customers.DN, 'ou=customers,dc=my-domain,dc=com')
        self.assertEqual(customers.name, 'ou=customers')
        self.assertEqual(customers.rdn_attr, 'ou')

        # Customers child keys
        self.assertEqual(customers.keys(), [
            u'ou=customer1', u'ou=customer2',
            u'ou=n\xe4sty\\, customer', u'uid=binary'
        ])

        # Customer has not been changed
        self.assertFalse(customers.changed)

    def test_binary_data(self):
        # Access existing binary data
        root = LDAPNode('dc=my-domain,dc=com', props)
        customers = root['ou=customers']
        binnode = customers['uid=binary']

        self.assertEqual(
            binnode.attrs['jpegPhoto'][:20],
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x01,\x01,\x00\x00'
        )
        self.assertEqual(len(binnode.attrs['jpegPhoto']), 2155)

        # Change binary data
        path = os.path.join(
            os.path.dirname(__file__),
            '..', 'testing', 'data', 'binary.jpg'
        )
        with open(path, 'rb') as f:
            jpegdata = f.read()

        self.assertTrue(customers is binnode.parent)
        self.assertFalse(binnode._action == ACTION_MODIFY)
        self.assertEqual(customers._modified_children, set())
        self.assertEqual(binnode.parent._modified_children, set())
        self.assertTrue(
            customers._modified_children is binnode.parent._modified_children
        )

        binnode.attrs['jpegPhoto'] = jpegdata
        self.assertTrue(binnode._action == ACTION_MODIFY)
        self.assertTrue(
            customers._modified_children is binnode.parent._modified_children
        )

        self.assertEqual(customers._modified_children, set(['uid=binary']))
        self.assertEqual(binnode.parent._modified_children, set(['uid=binary']))

        binnode()

        # Reload
        root = LDAPNode('dc=my-domain,dc=com', props)
        customers = root['ou=customers']
        binnode = customers['uid=binary']
        self.assertTrue(binnode.attrs['jpegPhoto'] == jpegdata)

    def test_tree_modification(self):
        root = LDAPNode('dc=my-domain,dc=com', props)
        customers = root['ou=customers']

        # Create new LDAPNode and add it to customers
        customer = LDAPNode()
        self.assertEqual(repr(customer), '<(dn not set) - False>')

        customer.attrs['ou'] = 'customer3'
        customer.attrs['description'] = 'customer3'
        customer.attrs['objectClass'] = ['top', 'organizationalUnit']

        # The already created node has not been attached to the tree, so
        # rdn_attr is not known yet
        self.assertEqual(customer.rdn_attr, None)

        # Also no DN and no LDAP session yet
        self.assertEqual(customer.DN, '')
        self.assertTrue(customer.ldap_session is None)
        self.assertEqual(customer.attrs['ou'], 'customer3')
        self.assertEqual(
            customer.attrs['objectClass'],
            ['top', 'organizationalUnit']
        )
        self.assertEqual(customer.keys(), [])

        # Tree has not changed yet
        self.check_output("""
        <dc=my-domain,dc=com - False>
          <ou=customers,dc=my-domain,dc=com:ou=customers - False>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        # Set already created customer
        customers['ou=customer3'] = customer
        self.assertEqual(
            customer.DN,
            'ou=customer3,ou=customers,dc=my-domain,dc=com'
        )
        self.assertEqual(customer.rdn_attr, 'ou')

        # Now it got the LDAP session which is used by the whole tree
        self.assertTrue(isinstance(customer.ldap_session, LDAPSession))
        self.assertTrue(root.ldap_session is customer.ldap_session)

        # Check added node internal DN
        self.assertEqual(
            customer._dn,
            'ou=customer3,ou=customers,dc=my-domain,dc=com'
        )

        # Data has changed in memory, but not persisted yet to LDAP
        self.assertEqual(customers.keys(), [
            u'ou=customer1',
            u'ou=customer2',
            u'ou=n\xe4sty\\, customer',
            u'uid=binary',
            u'ou=customer3'
        ])

        # Now tree nodes from customer up to root are flagged changed after
        # adding the new node
        self.check_output("""
        <dc=my-domain,dc=com - True>
          <ou=customers,dc=my-domain,dc=com:ou=customers - True>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
            <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        # New entry has no children, but was added to the parent. There
        # was a bug where iteration tried to load from ldap at this stage.
        # Lets test if this works
        self.assertEqual(customer.keys(), [])

        # The Container has changed...
        self.assertTrue(customers.changed)

        # ...but there's no action on the container since a child was added and
        # the attributes of the contained has not been changed
        self.assertEqual(customers._action, None)

        # The added child has been flagged changed as well...
        self.assertTrue(customer.changed)

        # ...and now there's also the action set that it has to be added
        self.assertTrue(customer._action is ACTION_ADD)

        # Check the backend state, not added yet
        res = customers.ldap_session.search(
            '(objectClass=*)',
            1,
            baseDN=customers.DN,
            force_reload=True
        )
        self.assertEqual(len(res), 4)

        # On call the new entry is written to the directory
        root()
        res = customers.ldap_session.search(
            '(objectClass=*)',
            1,
            baseDN=customers.DN,
            force_reload=True
        )
        self.assertEqual(len(res), 5)

        # All nodes are flagged unchanged again
        self.check_output("""
        <dc=my-domain,dc=com - False>
          <ou=customers,dc=my-domain,dc=com:ou=customers - False>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
            <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        # Add a person for more modification and changed flag tests
        person = LDAPNode()
        person.attrs['objectClass'] = ['top', 'person']
        person.attrs['sn'] = 'Mustermann'
        person.attrs['cn'] = 'Max'
        person.attrs['description'] = 'Initial Description'
        customer['cn=max'] = person

        self.assertEqual(customer.keys(), ['cn=max'])
        self.assertEqual(
            person.DN,
            'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com'
        )

        # Again, not in directory yet
        res = customer.ldap_session.search(
            '(objectClass=person)',
            1,
            baseDN=customer.DN,
            force_reload=True
        )
        self.assertEqual(len(res), 0)

        # Change the container of the person
        customer.attrs['street'] = 'foo'

        # Tell the person to commit its changes. The container (customer3) is
        # still changed because of its changed attributes
        self.assertEqual(customer._added_children, set(['cn=max']))

        person()
        self.assertEqual(customer._added_children, set())
        self.check_output("""
        <dc=my-domain,dc=com - True>
          <ou=customers,dc=my-domain,dc=com:ou=customers - True>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
            <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
              <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - False>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        # Call customer now, whole tree unchanged again
        customer()
        self.check_output("""
        <dc=my-domain,dc=com - False>
          <ou=customers,dc=my-domain,dc=com:ou=customers - False>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
            <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
              <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - False>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        # Change the person and customer again, and discard the attribute change
        # of the customer. It must not delete the changed state of the whole
        # tree, as the person is still changed
        customer.attrs['street'] = 'foo'
        person.attrs['description'] = 'foo'
        self.check_output("""
        <dc=my-domain,dc=com - True>
          <ou=customers,dc=my-domain,dc=com:ou=customers - True>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
            <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
              <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - True>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        self.assertTrue(person.nodespaces['__attrs__'].changed)
        self.assertTrue(person._changed)
        self.assertTrue(customer.nodespaces['__attrs__'].changed)
        self.assertTrue(customer._changed)

        customer.attrs.load()

        self.assertTrue(person.nodespaces['__attrs__'].changed)
        self.assertTrue(person._changed)
        self.assertFalse(customer.nodespaces['__attrs__'].changed)
        self.assertTrue(customer._changed)

        self.check_output("""
        <dc=my-domain,dc=com - True>
          <ou=customers,dc=my-domain,dc=com:ou=customers - True>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
            <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
              <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - True>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        # After calling person, whole tree is unchanged again
        person()
        self.check_output("""
        <dc=my-domain,dc=com - False>
          <ou=customers,dc=my-domain,dc=com:ou=customers - False>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
            <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
              <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - False>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        # Changing attributes of a node, where keys are not loaded, yet
        dn = 'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com'
        tmp = LDAPNode(dn, props=props)
        tmp.attrs['description'] = 'Initial Description'
        tmp()

        # Check set child immediately after init time
        tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
        tmp['cn=child'] = LDAPNode()
        self.assertEqual(tmp.keys(), [
            u'ou=customer1', u'ou=customer2', u'ou=n\xe4sty\\, customer',
            u'uid=binary', u'ou=customer3', u'cn=child'
        ])

        # Changing the rdn attribute on loaded nodes fails.
        person.attrs['cn'] = 'foo'
        err = self.expect_error(ldap.NAMING_VIOLATION, person.__call__)
        self.assertEqual(err.args[0], {
            'msgtype': 103,
            'msgid': 92,
            'result': 64,
            'desc': 'Naming violation',
            'ctrls': [],
            'info': "value of naming attribute 'cn' is not present in entry"
        })

        person.attrs.load()
        self.assertEqual(person.attrs['cn'], 'Max')

        # More attributes modification tests. Create Customer convenience query
        # function for later tests.

        def queryPersonDirectly():
            return customer.ldap_session.search(
                '(objectClass=person)',
                1,
                baseDN=customer.DN,
                force_reload=True
            )

        res = queryPersonDirectly()
        self.assertEqual(
            res[0][0],
            'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com'
        )
        self.assertEqual(sorted(res[0][1].items()), [
            ('cn', [b'Max']),
            ('description', [b'Initial Description']),
            ('objectClass', [b'top', b'person']),
            ('sn', [b'Mustermann'])
        ])

        # Modify this person. First look at the changed flags
        self.assertEqual(
            (root.changed, customer.changed, person.changed),
            (False, False, False)
        )
        self.assertEqual(person._action, None)
        self.assertFalse(person.attrs.changed)

        # Modify and check flags again
        person.attrs['description'] = 'Another description'
        self.assertTrue(person.attrs.changed)
        self.assertTrue(person._action == ACTION_MODIFY)
        self.assertEqual(
            (root.changed, customer.changed, person.changed),
            (True, True, True)
        )

        # Write changed to directory
        root()

        # Check the flags
        self.assertEqual(
            (root.changed, customer.changed, person.changed),
            (False, False, False)
        )

        # And check the changes in the directory
        res = queryPersonDirectly()
        self.assertEqual(
            res[0][0],
            'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com'
        )
        self.assertEqual(sorted(res[0][1].items()), [
            ('cn', [b'Max']),
            ('description', [b'Another description']),
            ('objectClass', [b'top', b'person']),
            ('sn', [b'Mustermann'])
        ])

        # Check removing of an attribute. This can be done by calling
        # __delitem__
        self.assertEqual(
            (root.changed, customer.changed, person.changed, person.attrs.changed),
            (False, False, False, False)
        )

        del person.attrs['description']
        self.assertEqual(
            (root.changed, customer.changed, person.changed, person.attrs.changed),
            (True, True, True, True)
        )
        person()

        res = queryPersonDirectly()
        self.assertEqual(
            res[0][0],
            'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com'
        )
        self.assertEqual(sorted(res[0][1].items()), [
            ('cn', [b'Max']),
            ('objectClass', [b'top', b'person']),
            ('sn', [b'Mustermann'])
        ])

        # Attributes are also removed by setting and empty string or UNSET.
        # Most LDAP implementations not allow setting empty values, thus
        # we delete the entire attribute in this case
        person.attrs['description'] = 'foo'
        person()

        res = queryPersonDirectly()
        self.assertEqual(res[0][1]['description'], [b'foo'])

        person.attrs['description'] = ''
        person()

        res = queryPersonDirectly()
        self.assertFalse('description' in res[0][1])

        # Setting the description again with no value has no effect, it just
        # gets ignored
        person.attrs['description'] = ''
        self.assertEqual(
            (root.changed, customer.changed, person.changed, person.attrs.changed),
            (False, False, False, False)
        )

        # We can call a node somewhere in the middle
        person.attrs['sn'] = 'Musterfrau'
        self.assertEqual(
            (root.changed, customer.changed, person.changed, person.attrs.changed),
            (True, True, True, True)
        )

        customer()
        res = queryPersonDirectly()
        self.assertEqual(
            res[0][0],
            'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com'
        )
        self.assertEqual(sorted(res[0][1].items()), [
            ('cn', [b'Max']),
            ('objectClass', [b'top', b'person']),
            ('sn', [b'Musterfrau'])
        ])
        self.assertEqual(
            (root.changed, customer.changed, person.changed, person.attrs.changed),
            (False, False, False, False)
        )

        # Reset sn
        person.attrs['sn'] = 'Mustermann'

        # Check adding of an attribute
        person.attrs['description'] = u'Brandnew description'
        self.assertEqual(
            (root.changed, customer.changed, person.changed, person.attrs.changed),
            (True, True, True, True)
        )

        customer()
        res = queryPersonDirectly()
        self.assertEqual(
            res[0][0],
            'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com'
        )
        self.assertEqual(sorted(res[0][1].items()), [
            ('cn', [b'Max']),
            ('description', [b'Brandnew description']),
            ('objectClass', [b'top', b'person']),
            ('sn', [b'Mustermann'])
        ])
        self.assertEqual(
            (root.changed, customer.changed, person.changed, person.attrs.changed),
            (False, False, False, False)
        )

        person.attrs['sn'] = u'i\u0107'
        person()
        self.assertEqual(queryPersonDirectly()[0][1]['sn'][0], b'i\xc4\x87')

        person.attrs['sn'] = b'i\xc4\x87'
        person()
        self.assertEqual(queryPersonDirectly()[0][1]['sn'][0], b'i\xc4\x87')

        # XXX: Don't test this until we have proper binary attr support
        # Attribute with utf16 str fails
        # person.attrs['sn'] = '\xff\xfei\x00\x07\x01'
        # person()
        # queryPersonDirectly()[0][1]['sn'][0]
        # Traceback (most recent call last):
        #   ...
        # UnicodeDecodeError:
        #   'utf8' codec can't decode byte 0xff in position 0: unexpected code byte

        # Check access to attributes on a fresh but added-to-parent node. There
        # was a bug so we test it. Note that rdn attribute is computed from key
        # if not set yet
        self.assertEqual(customers._added_children, set())
        self.assertEqual(customers._modified_children, set())

        customerattrempty = LDAPNode()
        self.assertEqual(customerattrempty._action, None)

        customers['cn=customer99'] = customerattrempty
        self.assertEqual(customers._added_children, set(['cn=customer99']))
        self.assertEqual(customers._modified_children, set())
        self.assertEqual(customerattrempty.attrs.keys(), ['cn'])
        self.assertEqual(customerattrempty._action, ACTION_ADD)

        # Add some attributes to make call work
        customerattrempty.attrs['objectClass'] = [
            'organizationalRole',
            'simpleSecurityObject'
        ]
        customerattrempty.attrs['userPassword'] = 'fooo'

        # Check deleting of entries
        self.check_output("""
        <dc=my-domain,dc=com - True>
          <ou=customers,dc=my-domain,dc=com:ou=customers - True>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
            <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
              <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - False>
            <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - True>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        self.assertEqual(customer.storage.keys(), ['cn=max'])

        del customer['cn=max']
        self.assertEqual(
            (root.changed, customer.changed, person.changed, person.attrs.changed),
            (True, True, True, False)
        )
        self.assertEqual(customer.storage.keys(), ['cn=max'])
        self.assertEqual(customer._deleted_children, set(['cn=max']))
        self.assertEqual(customer.keys(), [])

        self.check_output("""
        <dc=my-domain,dc=com - True>
          <ou=customers,dc=my-domain,dc=com:ou=customers - True>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
            <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
            <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - True>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        customer()
        self.assertEqual(customer.storage.keys(), [])
        self.assertEqual(customer._deleted_children, set())
        self.assertEqual(queryPersonDirectly(), [])

        self.check_output("""
        <dc=my-domain,dc=com - True>
          <ou=customers,dc=my-domain,dc=com:ou=customers - True>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
            <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
            <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - True>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        self.assertEqual(
            (root.changed, customers.changed, customer.changed, customerattrempty.changed),
            (True, True, False, True)
        )
        self.assertTrue(customerattrempty.parent is customers)
        self.assertEqual(customers._added_children, set(['cn=customer99']))
        self.assertEqual(customers._modified_children, set())

        customerattrempty()
        self.assertEqual(
            (root.changed, customers.changed, customerattrempty.changed),
            (False, False, False)
        )

        self.check_output("""
        <dc=my-domain,dc=com - False>
          <ou=customers,dc=my-domain,dc=com:ou=customers - False>
            <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
            <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
            <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
            <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
            <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
            <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>
          <ou=demo,dc=my-domain,dc=com:ou=demo - False>
        """, root.treerepr())

        # Test LDAPNode.child_defaults. A default value can either be a string
        # or a callback accepting the container node and the child key with
        # which the new child gets added.
        defaults = {
            'objectClass': ['top', 'person'],
            'sn': lambda x, y: 'sn for %s' % y,
            'description': lambda x, y: 'Description for %s' % y,
        }

        # Define child defaults for customer. It's possible to set an
        # LDAPNodeDefaults instance if a custom callback context is desired
        customer.child_defaults = defaults
        person = LDAPNode()
        customer['cn=person_with_default1'] = person
        self.assertEqual(sorted(person.attrs.items()), [
            ('cn', 'person_with_default1'),
            ('description', 'Description for cn=person_with_default1'),
            ('objectClass', ['top', 'person']),
            ('sn', 'sn for cn=person_with_default1')
        ])

        person()
        del customer['cn=person_with_default1']
        customer()

        # It's possible to add other INode implementing objects than LDAPNode.
        # An ldap node gets created then and attrs are set from original node
        new = BaseNode()
        err = self.expect_error(
            ValueError,
            customer.__setitem__,
            'cn=from_other',
            new
        )
        expected = 'No attributes found on vessel, cannot convert'
        self.assertEqual(str(err), expected)

        new = AttributedNode()
        new.attrs['description'] = 'Not from defaults'
        customer['cn=from_other'] = new
        customer()
        self.assertEqual(
            repr(customer['cn=from_other']),
            '<cn=from_other,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=from_other - False>'
        )

        self.assertEqual(sorted(customer['cn=from_other'].attrs.items()), [
            ('cn', 'from_other'),
            ('description', 'Not from defaults'),
            ('objectClass', ['top', 'person']),
            ('sn', 'sn for cn=from_other')
        ])

        del customer['cn=from_other']
        customer()

        # Test invalidation. Initialize node
        node = LDAPNode('ou=customers,dc=my-domain,dc=com', props)
        self.check_output("""
        <ou=customers,dc=my-domain,dc=com - False>
          <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
          <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
          <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
          <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
          <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
          <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>
        """, node.treerepr())

        # Invalidate node, children are invalidated and attrs are loaded
        node.invalidate()
        self.assertEqual(node.storage, odict())

        # Reload entries
        self.check_output("""
        <ou=customers,dc=my-domain,dc=com - False>
          <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
          <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
          <ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
          <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
          <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
          <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>
        """, node.treerepr())

        # Change descripton and try to invalidate, fails
        node.attrs['description'] = 'changed description'
        err = self.expect_error(RuntimeError, node.invalidate)
        expected = 'Invalid tree state. Try to invalidate changed node.'
        self.assertEqual(str(err), expected)

        # Reload attrs, change child and try to invalidate again, also fails
        node.attrs.load()
        self.assertFalse(node.changed)

        node.invalidate()
        node['ou=customer1'].attrs['description'] = 'changed description'
        err = self.expect_error(RuntimeError, node.invalidate)
        expected = 'Invalid tree state. Try to invalidate changed node.'
        self.assertEqual(str(err), expected)

        # Reload child attrs and check internal node state only customer one
        # loaded
        node['ou=customer1'].attrs.load()
        self.assertFalse(node.changed)
        self.assertEqual(len(node.storage.values()), 1)
        self.assertEqual(
            repr(node.storage.values()[0]),
            '<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>'
        )

        # Reload all children and check node state
        self.assertEqual([repr(it) for it in node.values()], [
            '<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>',
            '<ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>',
            '<ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>',
            '<uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>',
            '<ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>',
            '<cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>'
        ])
        self.assertEqual([repr(it) for it in node.storage.values()], [
            '<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>',
            '<ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>',
            '<ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>',
            '<uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>',
            '<ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>',
            '<cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>'
        ])

        # Invalidate with given key invalidates only child
        node.invalidate('ou=customer1')
        self.assertEqual([repr(it) for it in node.storage.values()], [
            '<ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>',
            '<ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>',
            '<uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>',
            '<ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>',
            '<cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>'
        ])

        # Invalidate key not in memory does nothing
        node.invalidate('ou=notexistent')
        self.assertEqual([repr(it) for it in node.storage.values()], [
            '<ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>',
            '<ou=n?sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>',
            '<uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>',
            '<ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>',
            '<cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>'
        ])

        # Invalidate changed child fails
        node['ou=customer2'].attrs['description'] = 'changed description'
        err = self.expect_error(
            RuntimeError,
            node.invalidate,
            'ou=customer2'
        )
        expected = "Invalid tree state. Try to invalidate changed child node 'ou=customer2'."
        self.assertEqual(str(err), expected)

        del customers['ou=customer3']
        del customers['cn=customer99']
        customers()

    def test_search(self):
        # We can fetch nodes by DNs
        node = LDAPNode('dc=my-domain,dc=com', props)
        err = self.expect_error(
            ValueError,
            node.node_by_dn,
            'ou=customers,dc=invalid_base,dc=com'
        )
        self.assertEqual(
            str(err),
            'Invalid DN "ou=customers,dc=invalid_base,dc=com" for given base DN "dc=my-domain,dc=com"'
        )
        self.assertEqual(
            repr(node.node_by_dn('dc=my-domain,dc=com')),
            '<dc=my-domain,dc=com - False>'
        )
        self.assertEqual(
            repr(node.node_by_dn('ou=customers,dc=my-domain,dc=com')),
            '<ou=customers,dc=my-domain,dc=com:ou=customers - False>'
        )
        self.assertEqual(
            repr(node.node_by_dn('ou=demo,dc=my-domain,dc=com')),
            '<ou=demo,dc=my-domain,dc=com:ou=demo - False>'
        )
        self.assertEqual(
            node.node_by_dn('ou=inexistent,dc=my-domain,dc=com'),
            None
        )
        err = self.expect_error(
            ValueError,
            node.node_by_dn,
            'ou=inexistent,dc=my-domain,dc=com',
            strict=True
        )
        expected = 'Tree contains no node by given DN. Failed at RDN ou=inexistent'
        self.assertEqual(str(err), expected)

        # Default search scope is ONELEVEL
        self.assertEqual(node.search_scope, ONELEVEL)

        # No other default search criteria set
        self.assertEqual(node.search_filter, None)
        self.assertEqual(node.search_criteria, None)
        self.assertEqual(node.search_relation, None)

        # Search with no arguments given return children keys
        self.assertEqual(sorted(node.search()), [
            'ou=customers,dc=my-domain,dc=com',
            'ou=demo,dc=my-domain,dc=com'
        ])

        # Set default search scope to SUBTREE
        node.search_scope = SUBTREE
        self.assertEqual(sorted(node.search()), [
            u'dc=my-domain,dc=com',
            u'ou=customer1,ou=customers,dc=my-domain,dc=com',
            u'ou=customer2,ou=customers,dc=my-domain,dc=com',
            u'ou=customers,dc=my-domain,dc=com',
            u'ou=demo,dc=my-domain,dc=com',
            u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com',
            u'uid=binary,ou=customers,dc=my-domain,dc=com'
        ])

        # We can fetch node instances instead of DN's in search result
        res = [repr(it) for it in node.search(get_nodes=True)]
        self.assertEqual(sorted(res), [
            '<dc=my-domain,dc=com - False>',
            '<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>',
            '<ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>',
            '<ou=customers,dc=my-domain,dc=com:ou=customers - False>',
            '<ou=demo,dc=my-domain,dc=com:ou=demo - False>',
            '<ou=n?sty\\, customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\\, customer - False>',
            '<uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>'
        ])

        # Search with pagination
        res, cookie = node.search(page_size=5)
        self.assertEqual(sorted(res), [
            u'dc=my-domain,dc=com',
            u'ou=customer1,ou=customers,dc=my-domain,dc=com',
            u'ou=customer2,ou=customers,dc=my-domain,dc=com',
            u'ou=customers,dc=my-domain,dc=com',
            u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com'
        ])

        res, cookie = node.search(page_size=5, cookie=cookie)
        self.assertEqual(sorted(res), [
            u'ou=demo,dc=my-domain,dc=com',
            u'uid=binary,ou=customers,dc=my-domain,dc=com'
        ])

        self.assertEqual(cookie, b'')

        # Lets add a default search filter.
        filter = LDAPFilter('(objectClass=organizationalUnit)')
        node.search_filter = filter
        self.assertEqual(sorted(node.search()), [
            u'ou=customer1,ou=customers,dc=my-domain,dc=com',
            u'ou=customer2,ou=customers,dc=my-domain,dc=com',
            u'ou=customers,dc=my-domain,dc=com',
            u'ou=demo,dc=my-domain,dc=com',
            u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com',
        ])

        # The default search filter could also be a string::
        node.search_filter = '(objectClass=organizationalUnit)'
        self.assertEqual(sorted(node.search()), [
            u'ou=customer1,ou=customers,dc=my-domain,dc=com',
            u'ou=customer2,ou=customers,dc=my-domain,dc=com',
            u'ou=customers,dc=my-domain,dc=com',
            u'ou=demo,dc=my-domain,dc=com',
            u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com',
        ])

        # Its also possible to define default search criteria as dict
        node.search_criteria = {
            'businessCategory': 'customers',
        }
        self.assertEqual(sorted(node.search()), [
            u'ou=customer1,ou=customers,dc=my-domain,dc=com',
            u'ou=customer2,ou=customers,dc=my-domain,dc=com',
            u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com'
        ])

        node.search_criteria = {
            'businessCategory': 'customers_container',
        }
        self.assertEqual(node.search(), [u'ou=customers,dc=my-domain,dc=com'])

        # To get more information by search result, pass an attrlist to search
        # function
        self.assertEqual(node.search(attrlist=['rdn', 'description']), [
            (u'ou=customers,dc=my-domain,dc=com', {
                u'rdn': u'ou=customers',
                u'description': [u'customers']
            })
        ])

        self.assertEqual(
            node.search(attrlist=['rdn', 'description', 'businessCategory']),
            [(u'ou=customers,dc=my-domain,dc=com', {
                u'rdn': u'ou=customers',
                u'description': [u'customers'],
                u'businessCategory': [u'customers_container']
            })]
        )

        # We can also fetch nodes instead of DN here
        res = node.search(attrlist=['dn', 'description'], get_nodes=True)
        self.assertEqual(len(res), 1)
        self.assertEqual(
            repr(res[0][0]),
            '<ou=customers,dc=my-domain,dc=com:ou=customers - False>'
        )
        self.assertEqual(res[0][1], {
            u'dn': u'ou=customers,dc=my-domain,dc=com',
            u'description': [u'customers']
        })

        res = node.search(
            attrlist=['dn', 'description', 'businessCategory'],
            get_nodes=True
        )
        self.assertEqual(len(res), 1)
        self.assertEqual(
            repr(res[0][0]),
            '<ou=customers,dc=my-domain,dc=com:ou=customers - False>'
        )
        self.assertEqual(res[0][1], {
            u'dn': u'ou=customers,dc=my-domain,dc=com',
            u'description': [u'customers'],
            u'businessCategory': [u'customers_container']
        })

        # Test without defaults, defining search with keyword arguments
        node.searcg_filter = None
        node.search_criteria = None
        res = node.search(
            queryFilter='(objectClass=organizationalUnit)',
            criteria={'businessCategory': 'customers_container'}
        )
        self.assertEqual(res, [u'ou=customers,dc=my-domain,dc=com'])

        # Restrict with exact match wotks on 1-length results
        res = node.search(
            queryFilter='(objectClass=organizationalUnit)',
            criteria={'businessCategory': 'customers_container'},
            exact_match=True
        )
        self.assertEqual(res, [u'ou=customers,dc=my-domain,dc=com'])

        # Exact match fails on multi search results
        err = self.expect_error(
            ValueError,
            node.search,
            queryFilter='(objectClass=organizationalUnit)',
            exact_match=True
        )
        expected = 'Exact match asked but result not unique'
        self.assertEqual(str(err), expected)

        # Exact match also fails on zero length result
        err = self.expect_error(
            ValueError,
            node.search,
            queryFilter='(objectClass=inexistent)',
            exact_match=True
        )
        expected = 'Exact match asked but result length is zero'
        self.assertEqual(str(err), expected)

        # Test relation filter
        node['ou=customers']['uid=binary'].attrs['description'] = 'customers'
        node()
        node.searcg_filter = None
        node.search_criteria = None
        node.search_relation = 'description:businessCategory'
        rel_node = node['ou=customers']['uid=binary']
        self.assertEqual(sorted(node.search(relation_node=rel_node)), [
            u'ou=customer1,ou=customers,dc=my-domain,dc=com',
            u'ou=customer2,ou=customers,dc=my-domain,dc=com',
            u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com'
        ])

        self.assertEqual(
            node.search(relation='description:description', relation_node=rel_node),
            []
        )

        node.search_relation = None
        relation = LDAPRelationFilter(rel_node, 'description:description')
        self.assertEqual(
            repr(relation),
            "LDAPRelationFilter('(description=customers)')"
        )
        self.assertEqual(str(relation), '(description=customers)')
        self.assertEqual(
            node.search(relation=relation),
            [u'ou=customers,dc=my-domain,dc=com']
        )

        relation = LDAPRelationFilter(
            rel_node,
            'description:description|description:businessCategory'
        )
        self.assertEqual(
            str(relation),
            '(|(businessCategory=customers)(description=customers))'
        )
        self.assertEqual(sorted(node.search(relation=relation)), [
            u'ou=customer1,ou=customers,dc=my-domain,dc=com',
            u'ou=customer2,ou=customers,dc=my-domain,dc=com',
            u'ou=customers,dc=my-domain,dc=com',
            u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com'
        ])

        node.search_relation = relation
        self.assertEqual(sorted(node.search()), [
            u'ou=customer1,ou=customers,dc=my-domain,dc=com',
            u'ou=customer2,ou=customers,dc=my-domain,dc=com',
            u'ou=customers,dc=my-domain,dc=com',
            u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com'
        ])

        # Search with binary in attrlist
        node = LDAPNode('dc=my-domain,dc=com', props)
        node.search_scope = SUBTREE
        res = sorted(node.search(attrlist=['jpegPhoto']))
        self.assertEqual(
            res[1][0],
            u'ou=customer1,ou=customers,dc=my-domain,dc=com'
        )
        self.assertFalse('jpegPhoto' in res[1][1])
        self.assertEqual(
            res[-1][0],
            u'uid=binary,ou=customers,dc=my-domain,dc=com'
        )
        self.assertTrue('jpegPhoto' in res[-1][1])

        # Add and delete node without persisting in between
        root = LDAPNode('dc=my-domain,dc=com', props)
        directadd = root['ou=directadd'] = LDAPNode()
        directadd.attrs['ou'] = 'directadd'
        directadd.attrs['description'] = 'directadd'
        directadd.attrs['objectClass'] = ['top', 'organizationalUnit']
        del root['ou=directadd']
        root()
        self.assertEqual(root.keys(), [u'ou=customers', u'ou=demo'])

    def test_events(self):
        pushGlobalRegistry()

        node = LDAPNode('dc=my-domain,dc=com', props)
        events = list()

        # Provide a bucnh of printing subscribers for testing
        @adapter(INode, ILDAPNodeCreatedEvent)
        def test_node_created_event(obj, event):
            events.append("Created {}".format(event.object))
        provideHandler(test_node_created_event)

        @adapter(INode, ILDAPNodeAddedEvent)
        def test_node_added_event(obj, event):
            events.append("Added {}".format(event.object))
        provideHandler(test_node_added_event)

        @adapter(INode, ILDAPNodeModifiedEvent)
        def test_node_modified_event(obj, event):
            events.append("Modified {}".format(event.object))
        provideHandler(test_node_modified_event)

        @adapter(INode, ILDAPNodeDetachedEvent)
        def test_node_detached_event(obj, event):
            events.append("Detached {}".format(event.object))
        provideHandler(test_node_detached_event)

        @adapter(INode, ILDAPNodeRemovedEvent)
        def test_node_removed_event(obj, event):
            events.append("Removed {}".format(event.object))
        provideHandler(test_node_removed_event)

        # Check basic event notification with *added*
        objectEventNotify(LDAPNodeAddedEvent(node))
        self.assertEqual(events, ['Added <dc=my-domain,dc=com - False>'])
        events = list()

        # Check for each event type in context
        root = LDAPNode('dc=my-domain,dc=com', props)
        self.assertEqual(events, ['Created <dc=my-domain,dc=com - False>'])
        events = list()

        self.assertEqual(root.keys(), [u'ou=customers', u'ou=demo'])
        root.values()
        self.assertEqual(events, [
            'Created <(dn not set) - False>',
            'Created <(dn not set) - False>'
        ])
        events = list()

        # create empty node
        newnode = LDAPNode()
        self.assertEqual(events, ['Created <(dn not set) - False>'])
        events = list()

        # add new node
        root['ou=eventtest01'] = newnode
        self.assertEqual(
            events,
            ['Added <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>']
        )
        events = list()

        # modify attrs
        newnode.attrs['description'] = 'foobar'
        self.assertEqual(
            events,
            ['Modified <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>']
        )
        events = list()

        del newnode.attrs['description']
        self.assertEqual(
            events,
            ['Modified <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>']
        )
        events = list()

        # detach
        eventtest = root.detach('ou=eventtest01')
        self.assertEqual(
            events,
            ['Detached <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>']
        )
        events = list()

        root['ou=eventtest01'] = eventtest
        self.assertEqual(
            events,
            ['Added <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>']
        )
        events = list()

        # delete
        del root['ou=eventtest01']
        self.assertEqual(
            events,
            ['Removed <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>']
        )

        popGlobalRegistry()

    def test_schema_info(self):
        root = LDAPNode('dc=my-domain,dc=com', props)

        # Get schema information
        schema_info = root.schema_info
        self.assertTrue(isinstance(schema_info, LDAPSchemaInfo))
        self.assertTrue(root[u'ou=customers'].schema_info is schema_info)
