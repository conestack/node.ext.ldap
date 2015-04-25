Secondary Keys
--------------

Secondary keys and child DN's.

Note: Setting the DN as seckey only seem to work because it is returned by LDAP
search result and considered (XXX: discuss). Child DN's are always available
at _child_dns::

    >>> tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
    >>> del tmp['cn=customer99']
    >>> tmp()

Note -> if seckey attr is missing on LDAP entry, entry is skipped::

    >>> tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
    >>> tmp._seckey_attrs = ('cn',)
    >>> tmp.keys()
    [u'ou=customer1', 
    u'ou=customer2', 
    u'ou=n\xe4sty\\, 
    customer', 
    u'uid=binary',
    u'ou=customer3']

    >>> tmp = LDAPNode('ou=customers,dc=my-domain,dc=com', props=props)
    >>> tmp._seckey_attrs = ('dn',)
    >>> tmp.keys()
    [u'ou=customer1',
    u'ou=customer2',
    u'ou=n\xe4sty\\, customer',
    u'uid=binary',
    u'ou=customer3']

    >>> tmp._seckeys
    {'dn':
    {u'ou=customer2,ou=customers,dc=my-domain,dc=com': u'ou=customer2',
    u'ou=customer1,ou=customers,dc=my-domain,dc=com': u'ou=customer1',
    u'ou=customer3,ou=customers,dc=my-domain,dc=com': u'ou=customer3',
    u'uid=binary,ou=customers,dc=my-domain,dc=com':
    u'uid=binary',
    u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com': u'ou=n\xe4sty\\, customer'}}

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
    u'uid=binary',
    u'ou=customer3']

    >>> tmp._child_dns
    {u'ou=n\xe4sty\\, customer':
    u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com',
    u'ou=customer3':
    u'ou=customer3,ou=customers,dc=my-domain,dc=com',
    u'ou=customer2':
    u'ou=customer2,ou=customers,dc=my-domain,dc=com',
    u'ou=customer1':
    u'ou=customer1,ou=customers,dc=my-domain,dc=com',
    u'uid=binary':
    u'uid=binary,ou=customers,dc=my-domain,dc=com'}

    >>> tmp._seckeys
    {'dn':
    {u'ou=customer2,ou=customers,dc=my-domain,dc=com': u'ou=customer2',
    u'ou=customer1,ou=customers,dc=my-domain,dc=com': u'ou=customer1',
    u'ou=customer3,ou=customers,dc=my-domain,dc=com': u'ou=customer3',
    u'uid=binary,ou=customers,dc=my-domain,dc=com': u'uid=binary',
    u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com': u'ou=n\xe4sty\\, customer'},
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
    u'uid=binary',
    u'ou=customer3']

    >>> tmp._child_dns
    {u'ou=n\xe4sty\\, customer':
    u'ou=n\xe4sty\\2C customer,ou=customers,dc=my-domain,dc=com',
    u'ou=customer3':
    u'ou=customer3,ou=customers,dc=my-domain,dc=com',
    u'ou=customer2':
    u'ou=customer2,ou=customers,dc=my-domain,dc=com',
    u'ou=customer1': u'ou=customer1,ou=customers,dc=my-domain,dc=com',
    u'uid=binary':
    u'uid=binary,ou=customers,dc=my-domain,dc=com'}

    >>> print tmp._seckeys
    None

Experimental features
---------------------

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
    RuntimeError: Key not unique: description='Initial Description' (you may want to disable check_duplicates)

    >>> props.check_duplicates=False
    >>> node.keys()
    [u'Initial Description']
    >>> props.check_duplicates=True

    >>> node = LDAPNode(props=props, name=customer.DN)
    >>> node._key_attr = 'objectClass'
    >>> node.keys()
    Traceback (most recent call last):
      ...
    KeyError: u"Expected one value for 'objectClass' not 2: '['top', 'person']'."

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
        <ou=n?sty\2C customer,ou=customers,dc=my-domain,dc=com:ou=n?sty\, customer - False>
        <uid=binary,ou=customers,dc=my-domain,dc=com:uid=binary - False>
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
    RuntimeError: Key not unique: rdn='ou=customer3' (you may want to disable check_duplicates)

We need a different key. As a side-effect a filter will be used: '(cn=*)'::

    >>> node = LDAPNode(props=props, name=root.DN)
    >>> node.search_scope = SUBTREE
    >>> node._key_attr = 'cn'
    >>> node._rdn_attr = 'cn'
    >>> node.child_defaults = {'objectClass': ['top', 'person']}
    >>> node.keys()
    [u'cn_binary', u'Max']

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
    [u'cn_binary', u'foo']

    >>> node = LDAPNode(props=props, name=root.DN)
    >>> node['cn=foo'].attrs['objectClass']
    [u'top', u'person']