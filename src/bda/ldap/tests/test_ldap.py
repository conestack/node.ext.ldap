__author__ = """Robert Niederreiter <rnix@squarewave.at>"""
__docformat__ = 'plaintext'

import os
import unittest
import interlude
import zope.component
from pprint import pprint
from zope.testing import doctest
from zope.app.testing.placelesssetup import setUp, tearDown
from zope.configuration.xmlconfig import XMLConfig

import bda.ldap

optionflags = doctest.NORMALIZE_WHITESPACE | \
              doctest.ELLIPSIS | \
              doctest.REPORT_ONLY_FIRST_FAILURE

TESTFILES = [
#    '../base.txt',
     '../entry.txt',
]

def test_suite():
    setUp()
    XMLConfig('meta.zcml', zope.component)()
    XMLConfig('configure.zcml', bda.ldap)()
    return unittest.TestSuite([
        doctest.DocFileSuite(
            file, 
            optionflags=optionflags,
            globs={'interact': interlude.interact,
                   'pprint': pprint},
        ) for file in TESTFILES
    ])
    tearDown()

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite') 