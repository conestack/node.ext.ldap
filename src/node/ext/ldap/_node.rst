# -*- coding: utf-8 -*-

LDAP Nodes
==========

Test related imports::

    >>> from node.base import AttributedNode
    >>> from node.base import BaseNode
    >>> from node.ext.ldap import LDAPNode
    >>> from node.ext.ldap import LDAPProps
    >>> from node.ext.ldap._node import ACTION_ADD
    >>> from node.ext.ldap._node import ACTION_DELETE
    >>> from node.ext.ldap._node import ACTION_MODIFY
    >>> from node.ext.ldap.events import LDAPNodeAddedEvent
    >>> from node.ext.ldap.filter import LDAPFilter
    >>> from node.ext.ldap.filter import LDAPRelationFilter
    >>> from node.ext.ldap.interfaces import ILDAPNodeAddedEvent
    >>> from node.ext.ldap.interfaces import ILDAPNodeCreatedEvent
    >>> from node.ext.ldap.interfaces import ILDAPNodeDetachedEvent
    >>> from node.ext.ldap.interfaces import ILDAPNodeModifiedEvent
    >>> from node.ext.ldap.interfaces import ILDAPNodeRemovedEvent
    >>> from node.ext.ldap.scope import ONELEVEL
    >>> from node.ext.ldap.scope import SUBTREE
    >>> from node.ext.ldap.testing import props
    >>> from node.interfaces import INode
    >>> from plone.testing.zca import popGlobalRegistry
    >>> from plone.testing.zca import pushGlobalRegistry
    >>> from zope.component import adapter
    >>> from zope.component import provideHandler
    >>> from zope.component.event import objectEventNotify
    >>> import os

Root Node
---------

Create the root node. The Root node expects the initial base DN as name and
the server properties::

    >>> LDAPNode('dc=my-domain,dc=com')
    Traceback (most recent call last):
    ...
    ValueError: Wrong initialization.

    >>> LDAPNode(props=props)
    Traceback (most recent call last):
    ...
    ValueError: Wrong initialization.

    >>> root = LDAPNode('dc=my-domain,dc=com', props)
    >>> root
    <dc=my-domain,dc=com - False>

The non-unicode name got decoded::

    >>> root.name
    'dc=my-domain,dc=com'

    >>> root.rdn_attr
    'dc'

Check exists::

    >>> root.exists
    True

    >>> inexistent = LDAPNode('dc=other-domain,dc=com', props)
    >>> inexistent.exists
    False

LDAP attributes for DN are stored on ``attrs``::

    >>> root.attrs
    <LDAPNodeAttributes object 'dc=my-domain,dc=com' at ...>

The node has session::

    >>> root.ldap_session
    <node.ext.ldap.session.LDAPSession object at ...>

Check and modify attributes of root::

    >>> sorted(root.attrs.items())
    [('dc', 'my-domain'),
     ('o', 'my-organization'),
     ('objectClass', ['top', 'dcObject', 'organization'])]

    >>> root.attrs['o'] = 'foo'

On ``__call__`` data gets persisted::

    >>> root()
    >>> sorted(root.attrs.items())
    [('dc', 'my-domain'),
     ('o', 'foo'),
     ('objectClass', ['top', 'dcObject', 'organization'])] 

Recreate root and check changed attributes::

    >>> root = LDAPNode('dc=my-domain,dc=com', props)
    >>> root.attrs.items()
    [('objectClass', ['top', 'dcObject', 'organization']),
    ('dc', 'my-domain'),
    ('o', 'foo')]

Reset o::

    >>> root.attrs['o'] = 'my-organization'
    >>> root()

Check child keys of root::

    >>> root.keys()
    ['ou=customers', 'ou=demo']

Access inexistent child::

    >>> foo = root['foo']
    Traceback (most recent call last):
    ...
    KeyError: 'foo'

Existent Child Nodes
--------------------

Access existent child and its attributes::

    >>> customers = root['ou=customers']
    >>> customers
    <ou=customers,dc=my-domain,dc=com:ou=customers - False>

    >>> sorted(customers.attrs.items())
    [('businessCategory', 'customers_container'),
    ('description', 'customers'),
    ('objectClass', ['top', 'organizationalUnit']),
    ('ou', 'customers')]

    >>> customers.DN
    'ou=customers,dc=my-domain,dc=com'

    >>> customers.name
    'ou=customers'

    >>> customers.rdn_attr
    'ou'

Customers child keys::

    >>> customers.keys()
    ['ou=customer1', 'ou=customer2', 'ou=n\xe4sty\\, customer', 'uid=binary']

Customer has not been changed::

    >>> customers.changed
    False

Binary Data
-----------

Access existing binary data::

    >>> customers = root['ou=customers']
    >>> binnode = customers['uid=binary']

    >>> binnode.attrs['jpegPhoto'][:20]
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x01,\x01,\x00\x00'

    >>> len(binnode.attrs['jpegPhoto'])
    2155

Change binary data::

    >>> jpegdata = open(os.path.join(os.path.dirname(__file__), 'testing',
    ...                 'data', 'binary.jpg'), 'rb').read()

    >>> customers is binnode.parent
    True

    >>> binnode._action == ACTION_MODIFY
    False

    >>> customers._modified_children == set()
    True

    >>> binnode.parent._modified_children == set()
    True

    >>> customers._modified_children is binnode.parent._modified_children
    True

    >>> binnode.attrs['jpegPhoto'] = jpegdata

    >>> binnode._action == ACTION_MODIFY
    True

    >>> customers._modified_children is binnode.parent._modified_children
    True

    >>> customers._modified_children == set(['uid=binary'])
    True

    >>> binnode.parent._modified_children == set(['uid=binary'])
    True

    >>> binnode()

Reload::

    >>> root = LDAPNode('dc=my-domain,dc=com', props)
    >>> customers = root['ou=customers']
    >>> binnode = customers['uid=binary']
    >>> binnode.attrs['jpegPhoto'] == jpegdata
    True

Create New Node
---------------

Create new LDAPNode and add it to customers::

    >>> customer = LDAPNode()
    >>> repr(customer)
    '<(dn not set) - False>'

    >>> customer.attrs['ou'] = 'customer3'
    >>> customer.attrs['description'] = 'customer3'
    >>> customer.attrs['objectClass'] = ['top', 'organizationalUnit']

The already created node has not been attached to the tree, so rdn_attr is not
known yet::

    >>> print(customer.rdn_attr)
    None

Also no DN and no LDAP session yet::

    >>> customer.DN
    ''

    >>> customer.ldap_session is None
    True

    >>> customer.attrs['ou']
    'customer3'

    >>> customer.attrs['objectClass']
    ['top', 'organizationalUnit']

    >>> customer.keys()
    []

Tree has not changed yet::

    >>> root.printtree()
    <dc=my-domain,dc=com - False>
      <ou=customers,dc=my-domain,dc=com:ou=customers - False>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

Set already created customer::

    >>> customers['ou=customer3'] = customer
    >>> customer.DN
    'ou=customer3,ou=customers,dc=my-domain,dc=com'

    >>> customer.rdn_attr
    'ou'

Now it got the LDAP session which is used by the whole tree::

    >>> customer.ldap_session
    <node.ext.ldap.session.LDAPSession object at ...>

    >>> root.ldap_session is customer.ldap_session
    True

Check added node internal DN::

    >>> customer._dn
    'ou=customer3,ou=customers,dc=my-domain,dc=com'

Data has changed in memory, but not persisted yet to LDAP::

    >>> customers.keys()
    ['ou=customer1',
    'ou=customer2',
    'ou=n\xe4sty\\, customer',
    'uid=binary',
    'ou=customer3']

Now tree nodes from customer up to root are flagged changed after adding the
new node::

    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

New entry has no childs, but was added to the parent. There
was a bug where iteration tried to load from ldap at this stage. Lets test
if this works::

    >>> customer.keys()
    []

The Container has changed...::

    >>> customers.changed
    True

...but there's no action on the container since a child was added and the
attributes of the contained has not been changed::

    >>> print(customers._action)
    None

The added child has been flagged changed as well...::

    >>> customer.changed
    True

...and now there's also the action set that it has to be added::

    >>> customer._action is ACTION_ADD
    True

Check the backend state, not added yet::

    >>> res = customers.ldap_session.search('(objectClass=*)',
    ...                                     1,
    ...                                     baseDN=customers.DN,
    ...                                     force_reload=True)
    >>> len(res)
    4

On call the new entry is written to the directory::

    >>> root()
    >>> res = customers.ldap_session.search('(objectClass=*)',
    ...                                     1,
    ...                                     baseDN=customers.DN,
    ...                                     force_reload=True)
    >>> len(res)
    5

All nodes are flagged unchanged again::

    >>> root.printtree()
    <dc=my-domain,dc=com - False>
      <ou=customers,dc=my-domain,dc=com:ou=customers - False>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

Add a person for more modification and changed flag tests::

    >>> person = LDAPNode()
    >>> person.attrs['objectClass'] = ['top', 'person']
    >>> person.attrs['sn'] = 'Mustermann'
    >>> person.attrs['cn'] = 'Max'
    >>> person.attrs['description'] = 'Initial Description'
    >>> customer['cn=max'] = person
    >>> customer.keys()
    ['cn=max']

    >>> person.DN
    'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com'

Again, not in directory yet::

    >>> res = customer.ldap_session.search('(objectClass=person)',
    ...                                    1,
    ...                                    baseDN=customer.DN,
    ...                                    force_reload=True)
    >>> len(res)
    0

Change the container of the person::

    >>> customer.attrs['street'] = 'foo'

Tell the person to commit its changes. The container (customer3) is still
changed because of its changed attributes::

    >>> customer._added_children == set(['cn=max'])
    True

    >>> person()

    >>> customer._added_children == set([])
    True

    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
          <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - False>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

Call customer now, whole tree unchanged again::

    >>> customer()
    >>> root.printtree()
    <dc=my-domain,dc=com - False>
      <ou=customers,dc=my-domain,dc=com:ou=customers - False>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
          <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - False>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

Change the person and customer again, and discard the attribute change
of the customer. It must not delete the changed state of the whole tree, as the
person is still changed::

    >>> customer.attrs['street'] = 'foo'
    >>> person.attrs['description'] = 'foo'
    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
          <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - True>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

    >>> person.nodespaces['__attrs__'].changed
    True
    >>> person._changed
    True

    >>> customer.nodespaces['__attrs__'].changed
    True
    >>> customer._changed
    True

    >>> customer.attrs.load()

    >>> person.nodespaces['__attrs__'].changed
    True
    >>> person._changed
    True

    >>> customer.nodespaces['__attrs__'].changed
    False
    >>> customer._changed
    True

    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
          <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - True>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

After calling person, whole tree is unchanged again::

    >>> person()
    >>> root.printtree()
    <dc=my-domain,dc=com - False>
      <ou=customers,dc=my-domain,dc=com:ou=customers - False>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
          <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - False>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

Changing attributes of a node, where keys are not loaded, yet::

    >>> dn = 'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com'
    >>> tmp = LDAPNode(dn, props=props)
    >>> tmp.attrs['description'] = 'Initial Description'
    >>> tmp()

Check set child immediately after init time::

    >>> tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
    >>> tmp['cn=child'] = LDAPNode()
    >>> tmp.keys()
    ['ou=customer1', 'ou=customer2', 'ou=n\xe4sty\\, customer',
    'uid=binary', 'ou=customer3', 'cn=child']

Changing the rdn attribute on loaded nodes fails.::

    >>> person.attrs['cn'] = 'foo'
    >>> person()
    Traceback (most recent call last):
      ...
    ldap.NAMING_VIOLATION: ..."value of naming attribute 'cn'
    is not present in entry"...}

    >>> person.attrs.load()
    >>> person.attrs['cn']
    'Max'

More attributes modification tests. Create Customer convenience query function
for later tests.::

    >>> def queryPersonDirectly():
    ...     res = customer.ldap_session.search('(objectClass=person)',
    ...                                        1,
    ...                                        baseDN=customer.DN,
    ...                                        force_reload=True)
    ...     return res

    >>> pprint(queryPersonDirectly())
    [('cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com',
      {'cn': ['Max'],
       'description': ['Initial Description'],
       'objectClass': ['top', 'person'],
       'sn': ['Mustermann']})]

Modify this person. First look at the changed flags::

    >>> root.changed, customer.changed, person.changed
    (False, False, False)

    >>> print(person._action)
    None

    >>> person.attrs.changed
    False

Modify and check flags again::

    >>> person.attrs['description'] = 'Another description'
    >>> person.attrs.changed
    True

    >>> person._action == ACTION_MODIFY
    True

    >>> root.changed, customer.changed, person.changed
    (True, True, True)

Write changed to directory::

    >>> root()

Check the flags::

    >>> root.changed, customer.changed, person.changed
    (False, False, False)

And check the changes in the directory::

    >>> pprint(queryPersonDirectly())
    [('cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com',
      {'cn': ['Max'],
       'description': ['Another description'],
       'objectClass': ['top', 'person'],
       'sn': ['Mustermann']})]

Check removing of an attribute::

    >>> root.changed, customer.changed, person.changed, \
    ... person.attrs.changed
    (False, False, False, False)

    >>> del person.attrs['description']
    >>> root.changed, customer.changed, person.changed, \
    ... person.attrs.changed
    (True, True, True, True)

We can call a node in the middle::

    >>> customer()
    >>> pprint(queryPersonDirectly())
    [('cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com',
      {'cn': ['Max'],
      'objectClass': ['top', 'person'],
      'sn': ['Mustermann']})]

    >>> root.changed, customer.changed, person.changed, \
    ... person.attrs.changed
    (False, False, False, False)

Check adding of an attribute::

    >>> person.attrs['description'] = 'Brandnew description'
    >>> root.changed, customer.changed, person.changed, \
    ... person.attrs.changed
    (True, True, True, True)

    >>> customer()
    >>> pprint(queryPersonDirectly())
    [('cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com',
      {'cn': ['Max'],
       'description': ['Brandnew description'],
       'objectClass': ['top', 'person'],
       'sn': ['Mustermann']})]

    >>> root.changed, customer.changed, person.changed, \
    ... person.attrs.changed
    (False, False, False, False)

Attribute with non-ascii unicode returns as is::

    >>> person.attrs['sn'] = u'i\u0107'
    >>> person()
    >>> queryPersonDirectly()[0][1]['sn'][0] == u'i\u0107'
    True

Attribute with non-ascii str (utf8) returns as unicode::

    >>> person.attrs['sn'] = b'i\xc4\x87'
    >>> person()
    >>> queryPersonDirectly()[0][1]['sn'][0] == u'i\u0107'
    True

# XXX: Don't test this until we have proper binary attr support
#Attribute with utf16 str fails::

#::
#    >>> person.attrs['sn'] = '\xff\xfei\x00\x07\x01'
#    >>> person()
#    >>> queryPersonDirectly()[0][1]['sn'][0]
#    Traceback (most recent call last):
#    ...
#    UnicodeDecodeError:
#      'utf8' codec can't decode byte 0xff in position 0: unexpected code byte

Check access to attributes on a fresh but added-to-parent node. There was a bug
so we test it. Note that rdn attribute is computed from key if not set yet::

    >>> customers._added_children == set([])
    True

    >>> customers._modified_children == set([])
    True

    >>> customerattrempty = LDAPNode()
    >>> customerattrempty._action is None
    True

    >>> customers['cn=customer99'] = customerattrempty

    >>> customers._added_children == {'cn=customer99'}
    True

    >>> customers._modified_children == set([])
    True

    >>> customerattrempty.attrs.keys()
    ['cn']

    >>> customerattrempty._action == ACTION_ADD
    True

Add some attributes to make call work::

    >>> customerattrempty.attrs['objectClass'] = \
    ...     ['organizationalRole', 'simpleSecurityObject']
    >>> customerattrempty.attrs['userPassword'] = 'fooo'

Check deleting of entries::

    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
          <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - False>
        <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - True>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

    >>> [k for k in customer.storage.keys()]
    ['cn=max']

    >>> del customer['cn=max']
    >>> root.changed, customer.changed, person.changed, \
    ... person.attrs.changed
    (True, True, True, False)

    >>> [k for k in customer.storage.keys()]
    ['cn=max']

    >>> customer._deleted_children == {'cn=max'}
    True

    >>> customer.keys()
    []

    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
        <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - True>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

    >>> customer()

    >>> [k for k in customer.storage.keys()]
    []

    >>> customer._deleted_children == set([])
    True

    >>> queryPersonDirectly()
    []

    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
        <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - True>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

    >>> root.changed, customers.changed, customer.changed, \
    ...     customerattrempty.changed
    (True, True, False, True)

    >>> customerattrempty.parent is customers
    True

    >>> customers._added_children == {'cn=customer99'}
    True

    >>> customers._modified_children == set([])
    True

    >>> customerattrempty()

    >>> root.changed, customers.changed, customerattrempty.changed
    (False, False, False)

    >>> root.printtree()
    <dc=my-domain,dc=com - False>
      <ou=customers,dc=my-domain,dc=com:ou=customers - False>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
        <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

Test LDAPNode.child_defaults. A default value can either be a string or a
callback accepting the container node and the child key with which the new
child gets added.::

    >>> defaults = {
    ...     'objectClass': ['top', 'person'],
    ...     'sn': lambda x, y: 'sn for %s' % y,
    ...     'description': lambda x, y: 'Description for %s' % y,
    ... }

Define child defaults for customer. It's possible to set an LDAPNodeDefaults
instance if a custom callback context is desired::

    >>> customer.child_defaults = defaults
    >>> person = LDAPNode()
    >>> customer['cn=person_with_default1'] = person
    >>> person.attrs.items()
    [('cn', 'person_with_default1'), ('objectClass', ['top', 'person']),
    ('sn', 'sn for cn=person_with_default1'), ('description',
    'Description for cn=person_with_default1')]

    >>> person()
    >>> del customer['cn=person_with_default1']
    >>> customer()

It's possible to add other INode implementing objects than LDAPNode. An ldap
node gets created then and attrs are set from original node::

    >>> new = BaseNode()
    >>> customer['cn=from_other'] = new
    Traceback (most recent call last):
      ...
    ValueError: No attributes found on vessel, cannot convert

    >>> new = AttributedNode()
    >>> new.attrs['description'] = 'Not from defaults'
    >>> customer['cn=from_other'] = new
    >>> customer()
    >>> customer['cn=from_other']
    <cn=from_other,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=from_other - False>

    >>> customer['cn=from_other'].attrs.items()
    [('description', 'Not from defaults'),
    ('cn', 'from_other'),
    ('objectClass', ['top', 'person']),
    ('sn', 'sn for cn=from_other')]

    >>> del customer['cn=from_other']
    >>> customer()

Test invalidation. Initialize node::

    >>> node = LDAPNode('ou=customers,dc=my-domain,dc=com', props)
    >>> node.printtree()
    <ou=customers,dc=my-domain,dc=com - False>
      <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
      <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
      <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
      <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
      <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
      <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>

Invalidate node, children are invalidated and attrs are loaded::

    >>> node.invalidate()
    >>> node.storage
    odict()

Reload entries::

    >>> node.printtree()
    <ou=customers,dc=my-domain,dc=com - False>
      <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
      <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
      <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>
      <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
      <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
      <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>

Change descripton and try to invalidate, fails::

    >>> node.attrs['description'] = 'changed description'
    >>> node.invalidate()
    Traceback (most recent call last):
      ...
    RuntimeError: Invalid tree state. Try to invalidate changed node.

Reload attrs, change child and try to invalidate again, also fails::

    >>> node.attrs.load()
    >>> node.changed
    False

    >>> node.invalidate()
    >>> node['ou=customer1'].attrs['description'] = 'changed description'
    >>> node.invalidate()
    Traceback (most recent call last):
      ...
    RuntimeError: Invalid tree state. Try to invalidate changed node.

Reload child attrs and check internal node state only customer one loaded::

    >>> node['ou=customer1'].attrs.load()
    >>> node.changed
    False

    >>> node.storage.values()
    [<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>]

Reload all children and check node state::

    >>> node.values()
    [<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>,
    <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>,
    <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>,
    <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>,
    <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>,
    <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>]

    >>> node.storage.values()
    [<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>,
    <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>,
    <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>,
    <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>,
    <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>,
    <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>]

Invalidate with given key invalidates only child::

    >>> node.invalidate('ou=customer1')
    >>> node.storage.values()
    [<ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>,
    <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>,
    <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>,
    <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>,
    <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>]

Invalidate key not in memory does nothing::

    >>> node.invalidate('ou=notexistent')
    >>> node.storage.values()
    [<ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>,
    <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>,
    <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>,
    <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>,
    <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>]

Invalidate changed child fails::

    >>> node['ou=customer2'].attrs['description'] = 'changed description'
    >>> node.invalidate('ou=customer2')
    Traceback (most recent call last):
      ...
    RuntimeError: Invalid tree state. Try to invalidate changed child node 'ou=customer2'.

Search
------

We can fetch nodes by DN's::

    >>> node = LDAPNode('dc=my-domain,dc=com', props)
    >>> node.node_by_dn('ou=customers,dc=invalid_base,dc=com')
    Traceback (most recent call last):
      ...
    ValueError: Invalid base DN

    >>> node.node_by_dn('dc=my-domain,dc=com')
    <dc=my-domain,dc=com - False>

    >>> node.node_by_dn('ou=customers,dc=my-domain,dc=com')
    <ou=customers,dc=my-domain,dc=com:ou=customers - False>

    >>> node.node_by_dn('ou=demo,dc=my-domain,dc=com')
    <ou=demo,dc=my-domain,dc=com:ou=demo - False>

    >>> node.node_by_dn('ou=inexistent,dc=my-domain,dc=com')

    >>> node.node_by_dn('ou=inexistent,dc=my-domain,dc=com', strict=True)
    Traceback (most recent call last):
      ...
    ValueError: Tree contains no node by given DN. Failed at RDN ou=inexistent

Default search scope is ONELEVEL::

    >>> node.search_scope is ONELEVEL
    True

No other default search criteria set::

    >>> print(node.search_filter)
    None

    >>> print(node.search_criteria)
    None

    >>> print(node.search_relation)
    None

Search with no arguments given return childs keys::

    >>> sorted(node.search())
    ['ou=customers,dc=my-domain,dc=com', 'ou=demo,dc=my-domain,dc=com']

Set default search scope to SUBTREE::

    >>> node.search_scope = SUBTREE
    >>> sorted(node.search())
    ['cn=customer99,ou=customers,dc=my-domain,dc=com',
    'dc=my-domain,dc=com',
    'ou=customer1,ou=customers,dc=my-domain,dc=com',
    'ou=customer2,ou=customers,dc=my-domain,dc=com',
    'ou=customer3,ou=customers,dc=my-domain,dc=com',
    'ou=customers,dc=my-domain,dc=com',
    'ou=demo,dc=my-domain,dc=com',
    'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com',
    'uid=binary,ou=customers,dc=my-domain,dc=com']

We can fetch node instances instead of DN's in search result::

    >>> pprint(node.search(get_nodes=True))
    [<dc=my-domain,dc=com - False>,
    <ou=demo,dc=my-domain,dc=com:ou=demo - False>,
    <ou=customers,dc=my-domain,dc=com:ou=customers - False>,
    <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>,
    <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>,
    <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>,
    <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>,
    <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>,
    <ou=n...sty\, customer,ou=customers,dc=my-domain,dc=com:ou=n...sty\, customer - False>]


Search with pagination::

    >>> res, cookie = node.search(page_size=5)
    >>> res
    ['dc=my-domain,dc=com',
    'ou=customers,dc=my-domain,dc=com',
    'ou=customer1,ou=customers,dc=my-domain,dc=com',
    'ou=customer2,ou=customers,dc=my-domain,dc=com',
    'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com']

    >>> res, cookie = node.search(page_size=5, cookie=cookie)
    >>> res
    ['ou=demo,dc=my-domain,dc=com',
    'uid=binary,ou=customers,dc=my-domain,dc=com',
    'ou=customer3,ou=customers,dc=my-domain,dc=com',
    'cn=customer99,ou=customers,dc=my-domain,dc=com']

    >>> assert cookie == b''

Lets add a default search filter.::

    >>> filter = LDAPFilter('(objectClass=organizationalUnit)')
    >>> node.search_filter = filter
    >>> node.search()
    ['ou=customers,dc=my-domain,dc=com',
    'ou=customer1,ou=customers,dc=my-domain,dc=com',
    'ou=customer2,ou=customers,dc=my-domain,dc=com',
    'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com',
    'ou=demo,dc=my-domain,dc=com',
    'ou=customer3,ou=customers,dc=my-domain,dc=com']

The default search filter could also be a string::

    >>> node.search_filter = '(objectClass=organizationalUnit)'
    >>> node.search()
    ['ou=customers,dc=my-domain,dc=com',
    'ou=customer1,ou=customers,dc=my-domain,dc=com',
    'ou=customer2,ou=customers,dc=my-domain,dc=com',
    'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com',
    'ou=demo,dc=my-domain,dc=com',
    'ou=customer3,ou=customers,dc=my-domain,dc=com']

Its also possible to define default search criteria as dict::

    >>> node.search_criteria = {
    ...     'businessCategory': 'customers',
    ... }
    >>> node.search()
    ['ou=customer1,ou=customers,dc=my-domain,dc=com',
    'ou=customer2,ou=customers,dc=my-domain,dc=com',
    'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com']

    >>> node.search_criteria = {
    ...     'businessCategory': 'customers_container',
    ... }
    >>> node.search()
    ['ou=customers,dc=my-domain,dc=com']

To get more information by search result, pass an attrlist to search function::

    >>> res = node.search(attrlist=['rdn', 'description'])
    >>> res[0][0]
    'ou=customers,dc=my-domain,dc=com'

    >>> res[0][1]['rdn']
    'ou=customers'

    >>> res[0][1]['description']
    ['customers']

    >>> res = node.search(attrlist=['rdn', 'description', 'businessCategory'])
    >>> res[0][0]
    'ou=customers,dc=my-domain,dc=com'

    >>> res[0][1]['rdn']
    'ou=customers'

    >>> res[0][1]['description']
    ['customers']

    >>> res[0][1]['businessCategory']
    ['customers_container']

We can also fetch nodes instead of DN here::

    >>> res = node.search(attrlist=['dn', 'description'],
    ...             get_nodes=True)
    >>> res[0][0]
    <ou=customers,dc=my-domain,dc=com:ou=customers - False>

    >>> res[0][1]['dn']
    'ou=customers,dc=my-domain,dc=com'

    >>> res = node.search(attrlist=['dn', 'description', 'businessCategory'],
    ...             get_nodes=True)
    >>> res[0][0]
    <ou=customers,dc=my-domain,dc=com:ou=customers - False>

    >>> res[0][1]['dn']
    'ou=customers,dc=my-domain,dc=com'

    >>> res[0][1]['description']
    ['customers']

    >>> res[0][1]['businessCategory']
    ['customers_container']

Test without defaults, defining search with keyword arguments::

    >>> node.search_filter = None
    >>> node.search_criteria = None
    >>> node.search(
    ...     queryFilter='(objectClass=organizationalUnit)',
    ...     criteria={'businessCategory': 'customers_container'})
    ['ou=customers,dc=my-domain,dc=com']

Restrict with exact match wotks on 1-length results::

    >>> node.search(
    ...     queryFilter='(objectClass=organizationalUnit)',
    ...     criteria={'businessCategory': 'customers_container'},
    ...     exact_match=True)
    ['ou=customers,dc=my-domain,dc=com']

Exact match fails on multi search results::

    >>> node.search(
    ...     queryFilter='(objectClass=organizationalUnit)',
    ...     exact_match=True)
    Traceback (most recent call last):
      ...
    ValueError: Exact match asked but result not unique

Exact match also fails on zero length result::

    >>> node.search(
    ...     queryFilter='(objectClass=inexistent)',
    ...     exact_match=True)
    Traceback (most recent call last):
      ...
    ValueError: Exact match asked but result length is zero

Test relation filter::

    >>> node['ou=customers']['cn=customer99'].attrs['description'] = 'customers'
    >>> node()
    >>> node.search_filter = None
    >>> node.search_criteria = None
    >>> node.search_relation = 'description:businessCategory'
    >>> rel_node = node['ou=customers']['cn=customer99']
    >>> node.search(relation_node=rel_node)
    ['ou=customer1,ou=customers,dc=my-domain,dc=com',
    'ou=customer2,ou=customers,dc=my-domain,dc=com',
    'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com']

    >>> node.search(relation='description:description', relation_node=rel_node)
    []

    >>> node.search_relation = None

    >>> relation = LDAPRelationFilter(rel_node, 'description:description')
    >>> relation
    LDAPRelationFilter('(description=customers)')

    >>> str(relation)
    '(description=customers)'

    >>> node.search(relation=relation)
    ['ou=customers,dc=my-domain,dc=com', 'cn=customer99,ou=customers,dc=my-domain,dc=com']

    >>> relation = LDAPRelationFilter(
    ...     rel_node, 'description:description|description:businessCategory')
    >>> str(relation)
    '(|(description=customers)(businessCategory=customers))'

    >>> node.search(relation=relation)
    ['ou=customers,dc=my-domain,dc=com',
    'ou=customer1,ou=customers,dc=my-domain,dc=com',
    'ou=customer2,ou=customers,dc=my-domain,dc=com',
    'cn=customer99,ou=customers,dc=my-domain,dc=com',
    'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com']

    >>> node.search_relation = relation
    >>> node.search()
    ['ou=customers,dc=my-domain,dc=com',
    'ou=customer1,ou=customers,dc=my-domain,dc=com',
    'ou=customer2,ou=customers,dc=my-domain,dc=com',
    'cn=customer99,ou=customers,dc=my-domain,dc=com',
    'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com']

Search with binary in attrlist::

    >>> node = LDAPNode('dc=my-domain,dc=com', props)
    >>> node.search_scope = SUBTREE
    >>> sorted(node.search(attrlist=['jpegPhoto']))
    [('cn=customer99,ou=customers,dc=my-domain,dc=com', {}),
    ('dc=my-domain,dc=com', {}),
    ('ou=customer1,ou=customers,dc=my-domain,dc=com', {}),
    ('ou=customer2,ou=customers,dc=my-domain,dc=com', {}),
    ('ou=customer3,ou=customers,dc=my-domain,dc=com', {}),
    ('ou=customers,dc=my-domain,dc=com', {}),
    ('ou=demo,dc=my-domain,dc=com', {}),
    ('ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com', {}),
    ('uid=binary,ou=customers,dc=my-domain,dc=com', {'jpegPhoto': [b'...']})]

Add and delete node without persisting in between::

    >>> root = LDAPNode('dc=my-domain,dc=com', props)
    >>> directadd = root['ou=directadd'] = LDAPNode()
    >>> directadd.attrs['o'] = 'directadd'
    >>> directadd.attrs['description'] = 'directadd'
    >>> directadd.attrs['objectClass'] = ['top', 'organizationalUnit']
    >>> del root['ou=directadd']
    >>> root()
    >>> root.keys()
    ['ou=customers', 'ou=demo']

Events
======

Use new registry::

    >>> reg = pushGlobalRegistry()

Provide a bucnh of printing subscribers for testing::

    >>> @adapter(INode, ILDAPNodeCreatedEvent)
    ... def test_node_created_event(obj, event):
    ...     print("Created {}".format(event.object))
    >>> provideHandler(test_node_created_event)

    >>> @adapter(INode, ILDAPNodeAddedEvent)
    ... def test_node_added_event(obj, event):
    ...     print("Added {}".format(event.object))
    >>> provideHandler(test_node_added_event)

    >>> @adapter(INode, ILDAPNodeModifiedEvent)
    ... def test_node_modified_event(obj, event):
    ...     print("Modified {}".format(event.object))
    >>> provideHandler(test_node_modified_event)

    >>> @adapter(INode, ILDAPNodeDetachedEvent)
    ... def test_node_detached_event(obj, event):
    ...     print("Detached {}".format(event.object))
    >>> provideHandler(test_node_detached_event)

    >>> @adapter(INode, ILDAPNodeRemovedEvent)
    ... def test_node_removed_event(obj, event):
    ...     print("Removed {}".format(event.object))
    >>> provideHandler(test_node_removed_event)

Check basic event notification with *added*::

    >>> objectEventNotify(LDAPNodeAddedEvent(node))
    Added <dc=my-domain,dc=com - False>

Check for each event type in context::

    >>> root = LDAPNode('dc=my-domain,dc=com', props)
    Created <dc=my-domain,dc=com - False>

    >>> root.keys()
    ['ou=customers', 'ou=demo']

    >>> dummy = root.items()
    Created <(dn not set) - False>
    Created <(dn not set) - False>

create empty node::

    >>> newnode = LDAPNode()
    Created <(dn not set) - False>

add new node::

    >>> root['ou=eventtest01'] = newnode
    Added <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>

modify attrs::

    >>> newnode.attrs['description'] = 'foobar'
    Modified <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>

    >>> del newnode.attrs['description']
    Modified <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>

detach::

    >>> eventtest = root.detach('ou=eventtest01')
    Detached <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>

    >>> root['ou=eventtest01'] = eventtest
    Added <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>

delete::

    >>> del root['ou=eventtest01']
    Removed <ou=eventtest01,dc=my-domain,dc=com:ou=eventtest01 - True>

Remove registry::

    >>> reg = popGlobalRegistry()

Schema Info
===========

Get schema information::

    >>> schema_info = root.schema_info
    >>> schema_info
    <node.ext.ldap.schema.LDAPSchemaInfo object at ...>

    >>> root['ou=customers'].schema_info is schema_info
    True

Clean
=====

Cleanup for following tests::

    >> root = LDAPNode('dc=my-domain,dc=com', props)
    >> del root['cn=foo']
    >> root()
