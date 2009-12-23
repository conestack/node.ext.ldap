# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

import time
import os
import subprocess
import unittest
import interlude
import pprint
from zope.testing import doctest

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
pr = subprocess.Popen([slapdbin, '-h', 'ldap://127.0.0.1:12345/'])
time.sleep(1)

TESTFILES = [
    'prepareslapd.txt',
    '../base.txt',
    '../session.txt',
    '../node.txt',
    'stopslapd.txt',
]

def test_suite():
    from zope.configuration.xmlconfig import XMLConfig
    import zope.component
    XMLConfig('meta.zcml', zope.component)()
    import bda.ldap
    XMLConfig('configure.zcml', bda.ldap)()
    return unittest.TestSuite([
        doctest.DocFileSuite(
            file, 
            optionflags=optionflags,
            globs={'interact': interlude.interact,
                   'pprint': pprint.pprint,
                  },
        ) for file in TESTFILES
    ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')