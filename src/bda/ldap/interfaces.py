# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

from zope.interface import Interface
from zope import schema

from bda.ldap.scope import ONELEVEL, SUBTREE


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
            description=u"e.g. ldap://localhost:389/",
            required=True,
            )
    
    user = schema.TextLine(
            title=u"Bind DN",
            description=u"DN used to bind to the ldap server.",
            required=True,
            )
    
    password = schema.TextLine(
            title=u"Bind password",
            description=u"Password used to bind to the ldap server.",
            required=True,
            )
    
    cache = schema.Bool(
            title=u"Cache",
            description=u"Enable caching",
            required=True,
            )
    
    timeout = schema.TextLine(
            title=u"Cache timeout",
            description=u"Cache timeout in seconds",
            default=600,
            required=True,
            )

#    start_tls = schema.TextLine(
#        title=u"start_tls",
#        description=u"",
#        required=True)
#
#    tls_cacertfile = schema.TextLine(
#        title=u"tls_cacertfile",
#        description=u"",
#        required=True)
#
#    tls_cacertdir = schema.TextLine(
#        title=u"tls_cacertdir",
#        description=u"",
#        required=True)
#
#    tls_clcertfile = schema.TextLine(
#        title=u"tls_clcertfile",
#        description=u"",
#        required=True)
#
#    tls_clkeyfile = schema.TextLine(
#        title=u"tls_clkeyfile",
#        description=u"",
#        required=True)
#
    retry_max = schema.TextLine(
            title=u"Retry max",
            description=u"Maximum number of reconnection attempts",
            default=1,
            required=True,
            )
    
    retry_delay = schema.TextLine(
            title=u"Retry delay",
            description=u"Delay between reconnection attempts",
            default=5.0,
            required=True,
            )


class ILDAPPrincipalsConfig(Interface):
    """
    """
    baseDN = schema.TextLine(
            title=u"Base DN",
            required=True,
            )

#    attrmap = schema.Dict(
#            title=u"Attribute mapping",
#            description=u"The minimum required is 'id' and 'login'."
#            required=True,
#            )
#
    scope = schema.Choice(
            title="Search scope",
            values=(ONELEVEL, SUBTREE),
            )

    queryFilter = schema.TextLine(
            title=u"Query filter"
            )


class ILDAPUsersConfig(ILDAPPrincipalsConfig):
    """LDAP users configuration interface.
    """


class ILDAPGroupsConfig(ILDAPPrincipalsConfig):
    """LDAP groups configuration interface.
    """
