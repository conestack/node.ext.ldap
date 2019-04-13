import sys
import unittest


def test_suite():
    from node.ext.ldap.tests import test_base
    from node.ext.ldap.tests import test_cache
    from node.ext.ldap.tests import test_filter
    from node.ext.ldap.tests import test_node
    from node.ext.ldap.tests import test_properties
    from node.ext.ldap.tests import test_schema
    from node.ext.ldap.tests import test_session

    suite = unittest.TestSuite()

    suite.addTest(unittest.findTestCases(test_base))
    suite.addTest(unittest.findTestCases(test_cache))
    suite.addTest(unittest.findTestCases(test_filter))
    suite.addTest(unittest.findTestCases(test_node))
    suite.addTest(unittest.findTestCases(test_properties))
    suite.addTest(unittest.findTestCases(test_schema))
    suite.addTest(unittest.findTestCases(test_session))

    return suite


def run_tests():
    from zope.testrunner.runner import Runner

    runner = Runner(found_suites=[test_suite()])
    runner.run()
    sys.exit(int(runner.failed))


if __name__ == '__main__':
    run_tests()
