import doctest
import interlude
import pprint
import unittest2 as unittest

from plone.testing import layered

from node.ext.ldap import testing


DOCFILES = [
    ('../base.txt', testing.LDIF_data),
    ('../session.txt', testing.LDIF_data),
    ('../_node.txt', testing.LDIF_data),
    ('../schema.txt', testing.LDIF_data),
    #('../users.txt', testing.LDIF_principals),
    #('../ugm_groupOfNames.txt', testing.LDIF_groupOfNames),
    #('../ugm_posixGroups.txt', testing.LDIF_posixGroups),
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
