node.ext.ldap.session
=====================

Test related imports::

    >>> from ldap import MOD_REPLACE
    >>> from node.ext.ldap import BASE
    >>> from node.ext.ldap import LDAPProps
    >>> from node.ext.ldap import LDAPSession
    >>> from node.ext.ldap import ONELEVEL
    >>> from node.ext.ldap import SUBTREE
    >>> from node.ext.ldap.testing import props

Create the session with ``LDAPProps`` as argument::

    >>> session = LDAPSession(props)
    >>> session.checkServerProperties()
    (True, 'OK')

There's no search base DN set yet:: 

    >>> session.baseDN
    ''

Set a baseDN and perform LDAP search::
  
    >>> session.baseDN = 'dc=my-domain,dc=com'
    >>> res = session.search('(objectClass=*)', SUBTREE)
    >>> len(res)
    7

Perform batched search::

    >>> session.baseDN = 'dc=my-domain,dc=com'
    >>> res, cookie = session.search('(objectClass=*)', SUBTREE, page_size=2)
    >>> assert cookie
    >>> len(res)
    2
    >>> res, cookie = session.search('(objectClass=*)', SUBTREE, page_size=2, cookie=cookie)
    >>> assert cookie
    >>> len(res)
    2
    >>> res, cookie = session.search('(objectClass=*)', SUBTREE, page_size=3, cookie=cookie)
    >>> assert not cookie
    >>> len(res)
    3
    >>> res, cookie = session.search('(objectClass=*)', SUBTREE, page_size=2, cookie=cookie)
    >>> len(res)
    2
    >>> res, cookie = session.search('(objectClass=*)', SUBTREE, page_size=2, cookie=cookie)
    >>> len(res)
    2

Add an entry::

    >>> entry = {
    ...     'cn':'foo',
    ...     'sn':'bar',
    ...     'objectclass':('person', 'top'),
    ... }
    >>> dn = 'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com'
    >>> session.add(dn, entry)
    >>> res = session.search('(objectClass=*)', SUBTREE)
    >>> len(res)
    8

Modify this entry and check the result::

    >>> res = session.search('(cn=foo)', SUBTREE)
    >>> res
    [('cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com', 
    {'objectClass': ['person', 'top'], 'cn': ['foo'], 'sn': ['bar']})]

    >>> session.modify(res[0][0], [(MOD_REPLACE, 'sn', 'baz')])
    >>> res = session.search('(cn=foo)', SUBTREE)
    >>> res
     [('cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com',
     {'objectClass': ['person', 'top'], 'cn': ['foo'], 'sn': ['baz']})]

Query only specific attributes::

    >>> res = session.search('(cn=foo)', SUBTREE, attrlist=('sn',))
    >>> res
    [('cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com', {'sn': ['baz']})]

And only the attributes without the values::

    >>> res = session.search('(cn=foo)', SUBTREE, attrlist=('sn',), attrsonly=True)
    >>> res
    [('cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com', {'sn': []})]

Delete this entry and check the result::

    >>> session.delete(res[0][0])
    >>> session.search('(cn=foo)', SUBTREE)
    []

Unbind from Server::

    >>> session.unbind()

Create the session with invalid ``LDAPProps``::

    >>> props = LDAPProps()
    >>> session = LDAPSession(props)
    >>> session.checkServerProperties()
    (False, SERVER_DOWN({'info': 'Transport endpoint is not connected', 
    'errno': 107, 'desc': "Can't contact LDAP server"},))
