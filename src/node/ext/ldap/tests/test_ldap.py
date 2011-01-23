# Copyright 2008-2010, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

import doctest
import interlude
import pprint
import unittest2 as unittest

from plone.testing import layered

from bda.ldap.testing import LDIF_data
from bda.ldap.testing import LDIF_principals


DOCFILES = [
    ('../base.txt', LDIF_data),
    ('../session.txt', LDIF_data),
    ('../node.txt', LDIF_data),
    ('../schema.txt', LDIF_data),
    ('../users.txt', LDIF_principals),
]

optionflags = doctest.NORMALIZE_WHITESPACE | \
              doctest.ELLIPSIS | \
              doctest.REPORT_ONLY_FIRST_FAILURE


print """
*******************************************************************************
If testing while development fails, please check if memcached is installed and
stop it if running.
*******************************************************************************
"""

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(
            doctest.DocFileSuite(
                docfile,
                globs={'interact': interlude.interact,
                           'pprint': pprint.pprint,
                           'pp': pprint.pprint,
                           },
                optionflags=optionflags,
                ),
            layer=layer,
            )
        for docfile, layer in DOCFILES
        ])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
