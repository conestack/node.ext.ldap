# -*- coding: utf-8 -*-

LDAP Nodes
==========

::

    >>> from node.ext.ldap import LDAPProps
    >>> from node.ext.ldap import LDAPNode
    >>> from node.ext.ldap.testing import props
    
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
    u'dc=my-domain,dc=com'
    
    >>> root.rdn_attr
    u'dc'

LDAP attributes for DN are stored on ``attrs``::

    >>> root.attrs
    <LDAPNodeAttributes object 'dc=my-domain,dc=com' at ...>

The node has session::

    >>> root.ldap_session
    <node.ext.ldap.session.LDAPSession object at ...>

Check and modify attributes of root::

    >>> root.attrs.items()
    [(u'objectClass', [u'top', u'dcObject', u'organization']),
     (u'dc', u'my-domain'),
     (u'o', u'my-organization')]

    >>> root.attrs['o'] = 'foo'

On ``__call__`` data gets persisted::

    >>> root()
    >>> root.attrs.items()
    [(u'objectClass', [u'top', u'dcObject', u'organization']),
     (u'dc', u'my-domain'),
     (u'o', u'foo')]

Recreate root and check changed attributes::

    >>> root = LDAPNode('dc=my-domain,dc=com', props)
    >>> root.attrs.items()
    [(u'objectClass', [u'top', u'dcObject', u'organization']), 
    (u'dc', u'my-domain'), 
    (u'o', u'foo')]

Reset o::

    >>> root.attrs['o'] = 'my-organization'
    >>> root()

Check child keys of root::

    >>> root.keys()
    [u'ou=customers', u'ou=demo']

Access inexistent child::

    >>> foo = root['foo']
    Traceback (most recent call last):
    ...
    KeyError: u'foo'
    
Existent Child Nodes
--------------------

Access existent child and it's attributes::
  
    >>> customers = root['ou=customers']
    >>> customers
    <ou=customers,dc=my-domain,dc=com:ou=customers - False>
  
    >>> customers.attrs.items()
    [(u'objectClass', [u'top', u'organizationalUnit']), 
    (u'ou', u'customers'), 
    (u'description', u'customers'), 
    (u'businessCategory', u'customers_container')]

    >>> customers.DN
    u'ou=customers,dc=my-domain,dc=com'

    >>> customers.name
    u'ou=customers'
    
    >>> customers.rdn_attr
    u'ou'

Customers child keys::

    >>> customers.keys()
    [u'ou=customer1', u'ou=customer2', u'ou=n\xe4sty\\, customer']

Customer has not been changed::

    >>> customers.changed
    False
    
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

    >>> print customer.rdn_attr
    None

Also no DN and no LDAP session yet::

    >>> customer.DN
    u''

    >>> customer.ldap_session is None
    True

    >>> customer.attrs['ou']
    u'customer3'
    
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
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

Set already created customer::

    >>> customers['ou=customer3'] = customer
    >>> customer.DN
    u'ou=customer3,ou=customers,dc=my-domain,dc=com'
    
    >>> customer.rdn_attr
    u'ou'

Now it got the LDAP session which is used by the whole tree::

    >>> customer.ldap_session
    <node.ext.ldap.session.LDAPSession object at ...>
    
    >>> root.ldap_session is customer.ldap_session
    True

Now tree nodes from customer up to root are flagged changed after adding the
new node::

    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

New entry has no childs, but was added to the parent. There
was a bug where iteration tried to load from ldap at this stage. Lets test
if this works::

    >>> customer.keys()
    []

Data has changed in memory, but not persisted yet to LDAP::

    >>> customers.keys()
    [u'ou=customer1', u'ou=customer2', u'ou=n\xe4sty\\, customer', u'ou=customer3']

The Container has changed...::
 
    >>> customers.changed
    True

...but there's no action on the container since a child was added and the
attributes of the contained has not been changed::

    >>> print customers._action
    None

The added child has been flagged changed as well...::

    >>> customer.changed
    True

...and now there's also the action set that it has to be added::

    >>> from node.ext.ldap._node import (
    ...     ACTION_ADD,
    ...     ACTION_MODIFY,
    ...     ACTION_DELETE,
    ... )
    >>> customer._action is ACTION_ADD
    True

Check the backend state, not added yet::

    >>> res = customers.ldap_session.search('(objectClass=*)',
    ...                                     1,
    ...                                     baseDN=customers.DN,
    ...                                     force_reload=True)
    >>> len(res)
    3

On call the new entry is written to the directory::
    
    >>> root()
    >>> res = customers.ldap_session.search('(objectClass=*)',
    ...                                     1,
    ...                                     baseDN=customers.DN,
    ...                                     force_reload=True)
    >>> len(res)
    4

All nodes are flagged unchanged again::

    >>> root.printtree()
    <dc=my-domain,dc=com - False>
      <ou=customers,dc=my-domain,dc=com:ou=customers - False>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
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
    [u'cn=max']
    
    >>> person.DN
    u'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com'
  
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

    >>> person()
    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
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
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
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
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
          <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - True>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>
    
    >>> customer.attrs.load()
    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
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
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
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
    [u'ou=customer1', u'ou=customer2', 
    u'ou=n\xe4sty\\, customer', u'ou=customer3', u'cn=child']

Changing the rdn attribute on loaded nodes fails.::

    >>> person.attrs['cn'] = 'foo'
    >>> person()
    Traceback (most recent call last):
      ...
    NAMING_VIOLATION: {'info': "value of naming attribute 'cn' 
    is not present in entry", 'desc': 'Naming violation'}
    
    >>> person.attrs.load()
    >>> person.attrs['cn']
    u'Max'

More attributes modification tests. Create Customer convenience query function
for later tests.::

    >>> def queryPersonDirectly():
    ...     res = customer.ldap_session.search('(objectClass=person)',
    ...                                        1,
    ...                                        baseDN=customer.DN,
    ...                                        force_reload=True)
    ...     return res
  
    >>> pprint(queryPersonDirectly())
    [(u'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com',
      {u'cn': [u'Max'],
       u'description': [u'Initial Description'],
       u'objectClass': [u'top', u'person'],
       u'sn': [u'Mustermann']})]

Modify this person. First look at the changed flags::

    >>> root.changed, customer.changed, person.changed
    (False, False, False)
  
    >>> print person._action
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
    [(u'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com',
      {u'cn': [u'Max'],
       u'description': [u'Another description'],
       u'objectClass': [u'top', u'person'],
       u'sn': [u'Mustermann']})]

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
    [(u'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com',
      {u'cn': [u'Max'], 
      u'objectClass': [u'top', u'person'], 
      u'sn': [u'Mustermann']})]

    >>> root.changed, customer.changed, person.changed, \
    ... person.attrs.changed
    (False, False, False, False)

Check adding of an attribute::

    >>> person.attrs['description'] = u'Brandnew description'
    >>> root.changed, customer.changed, person.changed, \
    ... person.attrs.changed
    (True, True, True, True)

    >>> customer()
    >>> pprint(queryPersonDirectly())
    [(u'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com',
      {u'cn': [u'Max'],
       u'description': [u'Brandnew description'],
       u'objectClass': [u'top', u'person'],
       u'sn': [u'Mustermann']})]

    >>> root.changed, customer.changed, person.changed, \
    ... person.attrs.changed
    (False, False, False, False)

Attribute with non-ascii unicode returns as is::

    >>> person.attrs['sn'] = u'i\u0107'
    >>> person()
    >>> queryPersonDirectly()[0][1]['sn'][0]
    u'i\u0107'

Attribute with non-ascii str (utf8) returns as unicode::

    >>> person.attrs['sn'] = 'i\xc4\x87'
    >>> person()
    >>> queryPersonDirectly()[0][1]['sn'][0]
    u'i\u0107'

# XXX: Don't test this until we have proper binary attr support
#Attribute with utf16 str fails::
#
#    >> person.attrs['sn'] = '\xff\xfei\x00\x07\x01'
#    Traceback (most recent call last):
#    ...
#    UnicodeDecodeError:
#      'utf8' codec can't decode byte 0xff in position 0: unexpected code byte

Check access to attributes on a fresh but added-to-parent node. There was a bug
so we test it. Note that rdn attribute is computed from key if not set yet::

    >>> customerattrempty = LDAPNode()
    >>> customers['cn=customer99'] = customerattrempty
    >>> customerattrempty.attrs.keys()
    [u'cn']

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
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
          <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - False>
        <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - True>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

    >>> [k for k in customer._keys]
    [u'cn=max']

    >>> del customer['cn=max']
    >>> root.changed, customer.changed, person.changed, \
    ... person.attrs.changed
    (True, True, True, False)
    
    >>> [k for k in customer._keys]
    []

    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - True>
        <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - True>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>
    
    >>> customer()
    >>> queryPersonDirectly()
    []

    >>> root.printtree()
    <dc=my-domain,dc=com - True>
      <ou=customers,dc=my-domain,dc=com:ou=customers - True>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
        <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - True>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>

    >>> root.changed, customer.changed
    (True, False)
    
    >>> customerattrempty()
    >>> root.printtree()
    <dc=my-domain,dc=com - False>
      <ou=customers,dc=my-domain,dc=com:ou=customers - False>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
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
    [(u'cn', u'person_with_default1'), 
    (u'objectClass', ['top', 'person']), 
    (u'sn', u'sn for cn=person_with_default1'), 
    (u'description', u'Description for cn=person_with_default1')]
    
    >>> person()
    >>> del customer['cn=person_with_default1']
    >>> customer()

It's possible to add other INode implementing objects than LDAPNode. An ldap
node gets created then and attrs are set from original node::

    >>> from node.base import BaseNode
    >>> new = BaseNode()
    >>> customer['cn=from_other'] = new
    Traceback (most recent call last):
      ...
    ValueError: No attributes found on vessel, cannot convert
    
    >>> from node.base import AttributedNode
    >>> new = AttributedNode()
    >>> new.attrs['description'] = 'Not from defaults'
    >>> customer['cn=from_other'] = new
    >>> customer()
    >>> customer['cn=from_other']
    <cn=from_other,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=from_other - False>
    
    >>> customer['cn=from_other'].attrs.items()
    [(u'description', u'Not from defaults'), 
    (u'cn', u'from_other'), 
    (u'objectClass', ['top', 'person']), 
    (u'sn', u'sn for cn=from_other')]
    
    >>> del customer['cn=from_other']
    >>> customer()

Test invalidation. Initialize node::

    >>> node = LDAPNode('ou=customers,dc=my-domain,dc=com', props)
    >>> node.printtree()
    <ou=customers,dc=my-domain,dc=com - False>
      <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
      <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
      <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
      <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
      <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>

Invalidate node, children are invalidated and attrs are loaded::

    >>> node.invalidate()
    >>> node.storage
    odict()
    
    >>> print node._keys
    None

Reload entries::

    >>> node.printtree()
    <ou=customers,dc=my-domain,dc=com - False>
      <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
      <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
      <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
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

Reload child attrs and check internal node statem only customer one loaded::

    >>> node['ou=customer1'].attrs.load()
    >>> node.changed
    False
    
    >>> node.storage.values()
    [<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>]
    
    >>> node._keys.values()
    [<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>, 
    None, 
    None, 
    None, 
    None]

Reload all children and check node state::

    >>> node.values()
    [<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>, 
    <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>, 
    <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>, 
    <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>, 
    <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>]
    
    >>> node.storage.values()
    [<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>, 
    <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>, 
    <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>, 
    <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>, 
    <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>]
    
    >>> node._keys.values()
    [<ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>, 
    <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>, 
    <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>, 
    <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>, 
    <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>]

Invalidate with given key invalidates only child::

    >>> node.invalidate('ou=customer1')
    >>> node.storage.values()
    [<ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>, 
    <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>, 
    <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>, 
    <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>]
    
    >>> node._keys.values()
    [None, 
    <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>, 
    <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>, 
    <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>, 
    <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>]

Invalidate changed child fails::

    >>> node['ou=customer2'].attrs['description'] = 'changed description'
    >>> node.invalidate('ou=customer2')
    Traceback (most recent call last):
      ...
    RuntimeError: Invalid tree state. Try to invalidate changed child node 'ou=customer2'.

Test search function::

    >>> from node.ext.ldap.scope import ONELEVEL, SUBTREE
    >>> node = LDAPNode('dc=my-domain,dc=com', props)

Default search scope is ONELEVEL::

    >>> node.search_scope is ONELEVEL
    True

No other default search criteria set::
    
    >>> print node.search_filter
    None
    
    >>> print node.search_criteria
    None
    
    >>> print node.search_relation
    None

Search with no arguments given return childs keys::

    >>> node.search()
    [u'ou=customers', u'ou=demo']

Set default search scope to SUBTREE. Be aware that this might not make much
sense, because of possible duplicate keys, since search with no other defaults
or passed arguments still returns only the keys. Though someone might use this
for counting entries::

    >>> node.search_scope = SUBTREE
    >>> node.search()
    [u'dc=my-domain', 
    u'ou=customers', 
    u'ou=customer1', 
    u'ou=customer2', 
    u'ou=n\xe4sty\\, customer', 
    u'ou=demo', 
    u'ou=customer3', 
    u'cn=customer99']

Lets add a default search filter.::

    >>> from node.ext.ldap.filter import LDAPFilter
    >>> filter = LDAPFilter('(objectClass=organizationalUnit)')
    >>> node.search_filter = filter
    >>> node.search()
    [u'ou=customers', 
    u'ou=customer1', 
    u'ou=customer2', 
    u'ou=n\xe4sty\\, customer', 
    u'ou=demo', 
    u'ou=customer3']

The default search filter could also be a string::

    >>> node.search_filter = '(objectClass=organizationalUnit)'
    >>> node.search()
    [u'ou=customers', 
    u'ou=customer1', 
    u'ou=customer2', 
    u'ou=n\xe4sty\\, customer', 
    u'ou=demo', 
    u'ou=customer3']

Its also possible to define default search criteria as dict::
    
    >>> node.search_criteria = {
    ...     'businessCategory': 'customers',
    ... }
    >>> node.search()
    [u'ou=customer1', 
    u'ou=customer2', 
    u'ou=n\xe4sty\\, customer']
    
    >>> node.search_criteria = {
    ...     'businessCategory': 'customers_container',
    ... }
    >>> node.search()
    [u'ou=customers']

To get more information by search result, pass an attrlist to search function::

    >>> node.search(attrlist=['dn', 'description'])
    [(u'ou=customers', 
    {'dn': u'ou=customers,dc=my-domain,dc=com', 
    u'description': [u'customers']})]
    
    >>> node.search(attrlist=['dn', 'description', 'businessCategory'])
    [(u'ou=customers', 
    {'dn': u'ou=customers,dc=my-domain,dc=com', 
    u'description': [u'customers'], 
    u'businessCategory': [u'customers_container']})]

Test withour defaults, defining search with keyword arguments::

    >>> node.searcg_filter = None
    >>> node.search_criteria = None
    >>> node.search(
    ...     queryFilter='(objectClass=organizationalUnit)',
    ...     criteria={'businessCategory': 'customers_container'})
    [u'ou=customers']

Restrict with exact match wotks on 1-length results::

    >>> node.search(
    ...     queryFilter='(objectClass=organizationalUnit)',
    ...     criteria={'businessCategory': 'customers_container'},
    ...     exact_match=True)
    [u'ou=customers']
    
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
    >>> node.searcg_filter = None
    >>> node.search_criteria = None
    >>> node.search_relation = 'description:businessCategory'
    >>> rel_node = node['ou=customers']['cn=customer99']
    >>> node.search(relation_node=rel_node)
    [u'ou=customer1', 
    u'ou=customer2', 
    u'ou=n\xe4sty\\, customer']
    
    >>> node.search(relation='description:description', relation_node=rel_node)
    []
    
    >>> node.search_relation = None
    
    >>> from node.ext.ldap.filter import LDAPRelationFilter
    >>> relation = LDAPRelationFilter(rel_node, 'description:description')
    >>> relation
    LDAPRelationFilter('(description=customers)')
    
    >>> str(relation)
    '(description=customers)'
    
    >>> node.search(relation=relation)
    [u'ou=customers']
    
    >>> relation = LDAPRelationFilter(
    ...     rel_node, 'description:description|description:businessCategory')
    >>> str(relation)
    '(|(description=customers)(businessCategory=customers))'
    
    >>> node.search(relation=relation)
    [u'ou=customers', 
    u'ou=customer1', 
    u'ou=customer2', 
    u'ou=n\xe4sty\\, customer']
    
    >>> node.search_relation = relation
    >>> node.search()
    [u'ou=customers', 
    u'ou=customer1', 
    u'ou=customer2', 
    u'ou=n\xe4sty\\, customer']

Secondary keys and child DN's.

Note: Setting the DN as seckey only seem to work because it is returned by LDAP
search result and considered (XXX: discuss). Child DN's are always available
at _child_dns::
    
    >>> tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
    >>> del tmp['cn=customer99']
    >>> tmp()
    
    >>> tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
    >>> tmp._seckey_attrs = ('cn',)
    >>> tmp.keys()
    Traceback (most recent call last):
      ...
    KeyError: u"Secondary key 'cn' missing on: 
    ou=customer1,ou=customers,dc=my-domain,dc=com."

    >>> tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
    >>> tmp._seckey_attrs = ('dn',)
    >>> tmp.keys()
    [u'ou=customer1', 
    u'ou=customer2', 
    u'ou=n\xe4sty\\, customer', 
    u'ou=customer3']
    
    >>> tmp._seckeys
    {'dn': 
    {u'ou=customer2,ou=customers,dc=my-domain,dc=com': u'ou=customer2', 
    u'ou=customer1,ou=customers,dc=my-domain,dc=com': u'ou=customer1', 
    u'ou=customer3,ou=customers,dc=my-domain,dc=com': u'ou=customer3', 
    u'ou=n\xe4sty\\2C customer,ou=Customers,dc=My-Domain,dc=com': u'ou=n\xe4sty\\, customer'}}
    
    >>> tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
    >>> tmp._seckey_attrs = ('description', 'businessCategory')
    >>> tmp.keys()
    Traceback (most recent call last):
      ...
    KeyError: u"Secondary key not unique: businessCategory='customers'."
    
    >>> tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
    >>> tmp._seckey_attrs = ('dn', 'objectClass')
    >>> tmp.keys()
    Traceback (most recent call last):
      ...
    KeyError: u"Expected one value for 
    'objectClass' not 2: '[u'top', u'organizationalUnit']'."

    >>> tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
    >>> tmp._seckey_attrs = ('dn', 'description')
    >>> tmp.keys()
    [u'ou=customer1', 
    u'ou=customer2', 
    u'ou=n\xe4sty\\, customer', 
    u'ou=customer3']
    
    >>> tmp._child_dns
    {u'ou=n\xe4sty\\, customer': 
    u'ou=n\xe4sty\\2C customer,ou=Customers,dc=My-Domain,dc=com', 
    u'ou=customer3': 
    u'ou=customer3,ou=customers,dc=my-domain,dc=com', 
    u'ou=customer2': 
    u'ou=customer2,ou=customers,dc=my-domain,dc=com', 
    u'ou=customer1': 
    u'ou=customer1,ou=customers,dc=my-domain,dc=com'}

    >>> tmp._seckeys
    {'dn': 
    {u'ou=customer2,ou=customers,dc=my-domain,dc=com': u'ou=customer2', 
    u'ou=customer1,ou=customers,dc=my-domain,dc=com': u'ou=customer1', 
    u'ou=customer3,ou=customers,dc=my-domain,dc=com': u'ou=customer3', 
    u'ou=n\xe4sty\\2C customer,ou=Customers,dc=My-Domain,dc=com': u'ou=n\xe4sty\\, customer'}, 
    'description': 
    {u'customer1': u'ou=customer1', 
    u'n\xe4sty': u'ou=n\xe4sty\\, customer', 
    u'customer3': u'ou=customer3', 
    u'customer2': u'ou=customer2'}}
    
    >>> tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
    >>> tmp.keys()
    [u'ou=customer1', 
    u'ou=customer2', 
    u'ou=n\xe4sty\\, customer', 
    u'ou=customer3']
    
    >>> tmp._child_dns
    {u'ou=n\xe4sty\\, customer': 
    u'ou=n\xe4sty\\2C customer,ou=Customers,dc=My-Domain,dc=com', 
    u'ou=customer3': 
    u'ou=customer3,ou=customers,dc=my-domain,dc=com', 
    u'ou=customer2': 
    u'ou=customer2,ou=customers,dc=my-domain,dc=com', 
    u'ou=customer1': 
    u'ou=customer1,ou=customers,dc=my-domain,dc=com'}
    
    >>> print tmp._seckeys
    None

###########################
Experimental features below
###########################

Using some other attribute as key, instead of the RDN. Let's first add two
person's the way we know it::

    >>> p1 = LDAPNode()
    >>> p1.attrs['objectClass'] = ['top', 'person']
    >>> p1.attrs['sn'] = 'Mustermann'
    >>> p1.attrs['cn'] = 'Max'
    >>> p1.attrs['description'] = 'Initial Description'
    >>> customer['cn=max'] = p1
    >>> p2 = LDAPNode()
    >>> p2.attrs['objectClass'] = ['top', 'person']
    >>> p2.attrs['sn'] = 'Mueller'
    >>> p2.attrs['cn'] = 'Moritz'
    >>> p2.attrs['description'] = 'Initial Description'
    >>> customer['cn=Moritz'] = p2
    >>> customer()
    >>> customer.keys()
    [u'cn=max', u'cn=Moritz']

Now choose some attribute as key, its value needs to be unique - XXX This is an
experimental feature, there must not be any children listing this node as a
parent!::

    >>> node = LDAPNode(props=props, name=customer.DN)
    >>> node._key_attr = 'description'
    >>> node.keys()
    Traceback (most recent call last):
    ...
    RuntimeError: Key not unique: description='Initial Description'.

    >>> node = LDAPNode(props=props, name=customer.DN)
    >>> node._key_attr = 'objectClass'
    >>> node.keys()
    Traceback (most recent call last):
      ...
    KeyError: u"Expected one value for 'objectClass' not 2: '[u'top', u'person']'."
    
    >>> node = LDAPNode(props=props, name=customer.DN)
    >>> node._key_attr = 'sn'
    >>> node.keys()
    [u'Mustermann', u'Mueller']

Childs can be retrieved normally::

    >>> our_p1 = node['Mustermann']
    >>> our_p1
    <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:Mustermann - False>

The node is the real parent::

    >>> our_p1.parent is node
    True

The child knows its correct DN::

    >>> our_p1.DN
    u'cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com'

We can change attributes::

    >>> our_p1.attrs['description'] = 'foo'
    >>> root.printtree()
    <dc=my-domain,dc=com - False>
      <ou=customers,dc=my-domain,dc=com:ou=customers - False>
        <ou=customer1,ou=customers,dc=my-domain,dc=com:ou=customer1 - False>
        <ou=customer2,ou=customers,dc=my-domain,dc=com:ou=customer2 - False>
        <ou=n?sty\2C customer,ou=Customers,dc=My-Domain,dc=com:ou=n?sty\, customer - False>
        <ou=customer3,ou=customers,dc=my-domain,dc=com:ou=customer3 - False>
          <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=max - False>
          <cn=Moritz,ou=customer3,ou=customers,dc=my-domain,dc=com:cn=Moritz - False>
        <cn=customer99,ou=customers,dc=my-domain,dc=com:cn=customer99 - False>
      <ou=demo,dc=my-domain,dc=com:ou=demo - False>
    
    >>> node.printtree()
    <ou=customer3,ou=customers,dc=my-domain,dc=com - True>
      <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:Mustermann - True>
      <cn=Moritz,ou=customer3,ou=customers,dc=my-domain,dc=com:Mueller - False>
    
    >>> our_p1()
    >>> node.printtree()
    <ou=customer3,ou=customers,dc=my-domain,dc=com - False>
      <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:Mustermann - False>
      <cn=Moritz,ou=customer3,ou=customers,dc=my-domain,dc=com:Mueller - False>
    
    >>> p1.attrs.load()
    >>> p1.attrs['description']
    u'foo'

Addings items, if _rdn_attr is set::

    >>> node['foo'] = LDAPNode()
    Traceback (most recent call last):
    ...
    RuntimeError: Adding with key != rdn needs _rdn_attr to be set.

    >>> node._rdn_attr = 'cn'
    >>> node['foo'] = LDAPNode()
    Traceback (most recent call last):
    ...
    ValueError: 'cn' needed in node attributes for rdn.

    >>> newnode = LDAPNode()
    >>> newnode.attrs['cn'] = 'newnode'
    >>> newnode.attrs['objectClass'] = ['top', 'person']

XXX: these need to be the same as 'sn' if used as key

::

    >>> newnode.attrs['sn'] = 'foo'
    >>> node['foo'] = newnode

    >>> node.keys()
    [u'Mustermann', u'Mueller', u'foo']

    >>> node['foo'] is newnode
    True

    >>> node is newnode.parent
    True

    >>> newnode.name == 'foo'
    True

Commit the added node::

    >>> node.printtree()
    <ou=customer3,ou=customers,dc=my-domain,dc=com - True>
      <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:Mustermann - False>
      <cn=Moritz,ou=customer3,ou=customers,dc=my-domain,dc=com:Mueller - False>
      <cn=newnode,ou=customer3,ou=customers,dc=my-domain,dc=com:foo - True>

    >>> node()
    >>> node.printtree()
    <ou=customer3,ou=customers,dc=my-domain,dc=com - False>
      <cn=max,ou=customer3,ou=customers,dc=my-domain,dc=com:Mustermann - False>
      <cn=Moritz,ou=customer3,ou=customers,dc=my-domain,dc=com:Mueller - False>
      <cn=newnode,ou=customer3,ou=customers,dc=my-domain,dc=com:foo - False>

    >>> node._reload = True
    >>> node.keys()
    [u'Mustermann', u'Mueller', u'foo']

    >>> node['foo'].attrs.items()
    [(u'objectClass', [u'top', u'person']),
     (u'cn', u'newnode'),
     (u'sn', u'foo')]

And deleting again::

    >>> del node['Mueller']
    >>> del node['foo']
    >>> node()
    >>> node.keys()
    [u'Mustermann']
    
    >>> node()
    >>> customer._reload = True
    >>> customer.keys()
    [u'cn=max']

Using filter and scope. Let's first create a collision::

    >>> tmp = LDAPNode()
    >>> tmp.attrs['ou'] = 'customer3'
    >>> tmp.attrs['objectClass'] = ['top', 'organizationalUnit']
    >>> root['ou=customer3'] = tmp
    >>> root()

    >>> from node.ext.ldap import SUBTREE
    >>> node = LDAPNode(props=props, name=root.DN)
    >>> node.search_scope = SUBTREE
    >>> node.keys()
    Traceback (most recent call last):
    ...
    RuntimeError: Key not unique: rdn='ou=customer3'.

We need a different key. As a side-effect a filter will be used: '(cn=*)'::

    >>> node = LDAPNode(props=props, name=root.DN)
    >>> node.search_scope = SUBTREE
    >>> node._key_attr = 'cn'
    >>> node._rdn_attr = 'cn'
    >>> node.child_defaults = {'objectClass': ['top', 'person']}
    >>> node.keys()
    [u'Max']

Again, we can query/change/delete these::

    >>> max = node['Max']
    >>> node['Max'].attrs['description'] = 'bar'
    >>> node()
    >>> max.attrs['description']
    u'bar'

New entries in case of scope SUBTREE are added in the ONELEVEL scope::

    >>> newnode = LDAPNode()
    >>> newnode.attrs['sn'] = 'foosn'
    >>> node['foo'] = newnode
    >>> node['foo'] is newnode
    True
    
    >>> newnode.DN
    u'cn=foo,dc=my-domain,dc=com'
    
    >>> node.DN
    u'dc=my-domain,dc=com'

    >>> del node['Max']
    >>> node()
    >>> node.keys()
    [u'foo']

    >>> node = LDAPNode(props=props, name=root.DN)
    >>> node['cn=foo'].attrs['objectClass']
    [u'top', u'person']

Events
======

Use new registry::

    >>> from plone.testing.zca import pushGlobalRegistry, popGlobalRegistry
    >>> reg = pushGlobalRegistry()
    
Provide a bucnh of printing subscribers for testing::
    
    >>> from zope.component import adapter, provideHandler
    >>> from node.ext.ldap.interfaces import (
    ...     ILDAPNodeCreatedEvent,
    ...     ILDAPNodeAddedEvent,
    ...     ILDAPNodeModifiedEvent,
    ...     ILDAPNodeDetachedEvent,
    ...     ILDAPNodeRemovedEvent,
    ... )
    >>> from node.interfaces import INode

    >>> @adapter(INode, ILDAPNodeCreatedEvent)
    ... def test_node_created_event(obj, event):
    ...     print "Created", event.object
    >>> provideHandler(test_node_created_event)

    >>> @adapter(INode, ILDAPNodeAddedEvent)
    ... def test_node_added_event(obj, event):
    ...     print "Added", event.object
    >>> provideHandler(test_node_added_event)

    >>> @adapter(INode, ILDAPNodeModifiedEvent)
    ... def test_node_modified_event(obj, event):
    ...     print "Modified", event.object
    >>> provideHandler(test_node_modified_event)

    >>> @adapter(INode, ILDAPNodeDetachedEvent)
    ... def test_node_detached_event(obj, event):
    ...     print "Detached", event.object
    >>> provideHandler(test_node_detached_event)

    >>> @adapter(INode, ILDAPNodeRemovedEvent)
    ... def test_node_removed_event(obj, event):
    ...     print "Removed", event.object
    >>> provideHandler(test_node_removed_event)

Check basic event notification with *added*::

    >>> from zope.component.event import objectEventNotify
    >>> from node.ext.ldap.events import LDAPNodeAddedEvent
    >>> objectEventNotify(LDAPNodeAddedEvent(node))
    Added <dc=my-domain,dc=com - False>

Check for each event type in context::

    >>> root = LDAPNode('dc=my-domain,dc=com', props)
    Created <dc=my-domain,dc=com - False>
    
    >>> dummy = root.items()
    Created <(dn not set) - False>
    Created <(dn not set) - False>
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


Clean
=====

Cleanup for following tests::

    >>> root = LDAPNode('dc=my-domain,dc=com', props)
    >>> del root['cn=foo']
    >>> root()
    
