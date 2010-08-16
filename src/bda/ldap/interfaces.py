# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

from zope.interface import Interface
from zope import schema

class ICacheProviderFactory(Interface):
    """Create some ICacheProvider implementing object on __call__.

    Must be registered as utility.
    """

    def __call__():
        """See above.
        """

class ILDAPProps(Interface):
    """LDAP properties configuration interface.
    """
    
    uri = schema.TextLine(
        title=u"URI",
        description=u"overrides server/port, forget about server and port, use"
                    u"this to specify how to access the ldap server",
        required=True)
    
    user = schema.TextLine(
        title=u"user",
        description=u"",
        required=True)
    
    password = schema.TextLine(
        title=u"password",
        description=u"",
        required=True)
    
    cache = schema.TextLine(
        title=u"cache",
        description=u"",
        required=True)
    
    timeout = schema.TextLine(
        title=u"timeout",
        description=u"",
        required=True)
    
    start_tls = schema.TextLine(
        title=u"start_tls",
        description=u"",
        required=True)
    
    tls_cacertfile = schema.TextLine(
        title=u"tls_cacertfile",
        description=u"",
        required=True)
    
    tls_cacertdir = schema.TextLine(
        title=u"tls_cacertdir",
        description=u"",
        required=True)
    
    tls_clcertfile = schema.TextLine(
        title=u"tls_clcertfile",
        description=u"",
        required=True)
    
    tls_clkeyfile = schema.TextLine(
        title=u"tls_clkeyfile",
        description=u"",
        required=True)
    
    retry_max = schema.TextLine(
        title=u"retry_max",
        description=u"",
        required=True)
    
    retry_delay = schema.TextLine(
        title=u"retry_delay",
        description=u"",
        required=True)


#XXX: ILDAPPrincipalsConfig
#XXX: make sure attrmap contains id for principals and login for users

class ILDAPGroupsConfig(Interface):
    """LDAP groups configuration interface.
    """
    
    props = schema.Object(
        title=u"LDAPProps object",              
        schema=ILDAPProps)
    
    baseDN = schema.TextLine(
        title=u"Base DN",
        required=True)
    
    id_attr = schema.TextLine(
        title=u"ID attribute name",
        required=True)
    
    #scope = schema.Choice(
    #    title="Scope for searching",
    #    vocabulary=None) # XXX
    scope = schema.TextLine(
        title=u"Scope for searching")
    
    queryFilter = schema.TextLine(
        title=u"Query filter")

class ILDAPUsersConfig(ILDAPGroupsConfig):
    """LDAP users configuration interface.
    """
    
    login_attr = schema.TextLine(
        title=u"login attribute name",
        required=True)
