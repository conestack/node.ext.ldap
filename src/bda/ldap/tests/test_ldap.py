__author__ = """Robert Niederreiter <rnix@squarewave.at>"""
__docformat__ = 'plaintext'

import time
import os
from subprocess import Popen
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

print """
*******************************************************************************
Starting openldap server...

If testing while development fails, please check if memcached is installed and
stop it if running.
*******************************************************************************
"""

slapdbin = os.environ.get('SLAPDBIN', None)
pr = Popen([slapdbin, '-h', 'ldap://127.0.0.1:12345/'])
slapdpid = pr.pid
time.sleep(1)

TESTFILES = [
    'prepareslapd.txt',
    '../base.txt',
    '../node.txt',
    'stopslapd.txt',
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
                   'pprint': pprint,
                   'slapdpid': slapdpid},
        ) for file in TESTFILES
    ])
    tearDown()

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')