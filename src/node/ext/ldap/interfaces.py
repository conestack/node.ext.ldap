# Copyright 2008-2010, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later
from zope.interface import (
    Interface,
    Attribute,
)

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

    uri = Attribute(u"LDAP URI")

    user = Attribute(u"LDAP User")

    password = Attribute(u"Bind Password")

    cache = Attribute(u"Flag wether to use cache or not")

    timeout = Attribute(u"Timeout in seconds")

    start_tls = Attribute(u"TLS enabled")

    tls_cacertfile = Attribute(u"Name of CA Cert file")

    tls_cacertdir = Attribute(u"Path to CA Cert directory")

    tls_clcertfile = Attribute(u"Name of CL Cert file")

    tls_clkeyfile = Attribute(u"Path to CL key file")

    retry_max = Attribute(u"Retry count")

    retry_delay = Attribute(u"Retry delay in seconds")

class ILDAPPrincipalsConfig(Interface):
    """LDAP principals configuration interface.
    """

    baseDN = Attribute(u"Principals base DN")

    attrmap = Attribute(u"Principals Attribute map as ``odict.odict``")

    scope = Attribute(u"Search scope for principals")

    queryFilter = Attribute(u"Query filter for principals")

    objectClasses = Attribute(u"Default object classes for new principals.")

class ILDAPUsersConfig(ILDAPPrincipalsConfig):
    """LDAP users configuration interface.
    """

class ILDAPGroupsConfig(ILDAPPrincipalsConfig):
    """LDAP groups configuration interface.
    """
