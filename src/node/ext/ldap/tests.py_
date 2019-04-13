# -*- coding: utf-8 -*-
from node.ext.ldap import testing
from plone.testing import layered
import doctest
import interlude
import pprint
import unittest


DOCFILES = [
    ('cache.rst', testing.LDIF_data),
    ('base.rst', testing.LDIF_data),
    ('session.rst', testing.LDIF_data),
    ('filter.rst', testing.LDIF_data),
    ('_node.rst', testing.LDIF_data),
    ('properties.rst', testing.LDIF_data),
    ('schema.rst', testing.LDIF_data),
    ('ugm/principals.rst', testing.LDIF_principals),
    ('ugm/groupOfNames.rst', testing.LDIF_groupOfNames),
    ('ugm/posixGroups.rst', testing.LDIF_posixGroups),
    ('ugm/sambaUsers.rst', testing.LDIF_sambaUsers),
    ('ugm/defaults.rst', testing.LDIF_data),
    ('../../../../README.rst', testing.LDIF_data),
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
            layer=layer)
        for docfile, layer in DOCFILES
    ])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')                #pragma NO COVERAGE
