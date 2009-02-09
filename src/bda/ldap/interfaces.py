#
# Copyright 2008, Blue Dynamics Alliance, Austria - http://bluedynamics.com
#
# GNU General Public Licence Version 2 or later

__author__ = """Robert Niederreiter <rnix@squarewave.at>"""
__docformat__ = 'plaintext'

from zope.interface import Interface

class ICacheProviderFactory(Interface):
    """Create some ICacheProvider implementing object on __call__.
    
    Must be registered as utility.
    """
    
    def __call__():
        """See above.
        """