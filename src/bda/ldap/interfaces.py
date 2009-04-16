# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

from zope.interface import Interface

class ICacheProviderFactory(Interface):
    """Create some ICacheProvider implementing object on __call__.
    
    Must be registered as utility.
    """
    
    def __call__():
        """See above.
        """