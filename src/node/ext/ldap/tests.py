# -*- coding: utf-8 -*-
from __future__ import print_function
from node.ext.ldap import testing
from plone.testing import layered
import doctest
import interlude
import pprint
import re
import six
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


print("""
*******************************************************************************
If testing while development fails, please check if memcached is installed and
stop it if running.
*******************************************************************************
""")


class Py23DocChecker(doctest.OutputChecker):

    def check_output(self, want, got, optionflags):
        if want != got and six.PY2:
            # if running on py2, ignore any "u" prefixes in the output
            got = re.sub("(\\W|^)u'(.*?)'", "\\1'\\2'", got)
            got = re.sub("(\\W|^)u\"(.*?)\"", "\\1\"\\2\"", got)
            # also ignore "b" prefixes in the expected output
            want = re.sub("b'(.*?)'", "'\\1'", want)
            # we get 'ldap.' prefixes on python 3, e.g.
            # ldap.UNWILLING_TO_PERFORM
            want = want.lstrip('ldap.')
        return doctest.OutputChecker.check_output(self, want, got, optionflags)


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
                checker=Py23DocChecker(),
            ),
            layer=layer)
        for docfile, layer in DOCFILES
    ])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')                #pragma NO COVERAGE
