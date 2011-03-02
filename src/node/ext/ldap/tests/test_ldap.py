# Copyright 2008-2010, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

import doctest
import interlude
import pprint
import unittest2 as unittest

from plone.testing import layered

from node.ext.ldap import testing


DOCFILES = [
    ('../base.txt', testing.LDIF_data),
    ('../session.txt', testing.LDIF_data),
    ('../bbb.txt', testing.LDIF_data),
    ('../schema.txt', testing.LDIF_data),
    ('../users.txt', testing.LDIF_principals),
    ('groupOfNames.txt', testing.LDIF_groupOfNames),
    ('groupOfNames_add.txt', testing.LDIF_groupOfNames_add),
    ]

optionflags = \
    doctest.NORMALIZE_WHITESPACE | \
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
