# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

from zope.interface import Interface
from zope.schema import TextLine, Choice


class ICacheProviderFactory(Interface):
    """Create some ICacheProvider implementing object on __call__.

    Must be registered as utility.
    """

    def __call__():
        """See above.  """


class ILDAPGroupsConfig(Interface):
    props = Object(schema=IProps)
    baseDN = TextLine(title="Base DN", required=True)
    id_attr = TextLine(title="ID attribute name", required=True)
    login_attr = TextLine(title="Login attribute name", required=True)
    scope = Choice(title="Scope for searching", vocabulary=)
    queryFilter = TextLine(title="Query filter")
