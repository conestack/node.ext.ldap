node.ext.ldap.session
=====================

::

    >>> from node.ext.ldap import BASE, ONELEVEL, SUBTREE
    >>> from node.ext.ldap import LDAPProps, LDAPSession
    >>> from node.ext.ldap.testing import props

Create the session with ``LDAPProps`` as argument::
    
    >>> session = LDAPSession(props)
    >>> session.checkServerProperties()
    (True, 'OK')

There's no search base DN set yet:: 

    >>> session.baseDN
    u''
    
Set a baseDN and perform LDAP search::
  
    >>> session.baseDN = 'dc=my-domain,dc=com'
    >>> from node.ext.ldap import SUBTREE
    >>> res = session.search('(objectClass=*)', SUBTREE)
    >>> len(res)
    6

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
    7

Modify this entry and check the result::

    >>> res = session.search('(cn=foo)', SUBTREE)
    >>> res
    [(u'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com', 
    {u'objectClass': [u'person', u'top'], u'cn': [u'foo'], u'sn': [u'bar']})]

    >>> from ldap import MOD_REPLACE
    >>> session.modify(res[0][0], [(MOD_REPLACE, 'sn', 'baz')])
    >>> res = session.search('(cn=foo)', SUBTREE)
    >>> res
    [(u'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com', 
    {u'objectClass': [u'person', u'top'], u'cn': [u'foo'], u'sn': [u'baz']})]

Query only specific attributes::

    >>> res = session.search('(cn=foo)', SUBTREE, attrlist=('sn',))
    >>> res
    [(u'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com', {u'sn': [u'baz']})]

And only the attributes without the values::

    >>> res = session.search('(cn=foo)', SUBTREE, attrlist=('sn',), attrsonly=True)
    >>> res
    [(u'cn=foo,ou=customer1,ou=customers,dc=my-domain,dc=com', {u'sn': []})]

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
    (False, SERVER_DOWN({'desc': "Can't contact LDAP server"},))
