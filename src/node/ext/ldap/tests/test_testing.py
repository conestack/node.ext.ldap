from contextlib import redirect_stdout
from node.ext.ldap import testing
from node.tests import NodeTestCase
from plone.testing import zca
from unittest import mock
import io
import os
import tempfile


# Set by ``node.ext.ldap.main.slapd`` to the slapd config directory
TESTLDAP_ENV = 'node.ext.ldap.testldap.env'


class TestTesting(NodeTestCase):
    def test_slapd_teardown_stops_server_started_by_slapd_script(self):
        slapd = testing.Slapd(bases=(), name='TestSlapd')
        with tempfile.TemporaryDirectory() as confdir:
            os.mkdir(os.path.join(confdir, 'openldap-data'))
            with open(os.path.join(confdir, 'slapd.pid'), 'w') as pidfile:
                pidfile.write('4711')
            with (
                mock.patch.dict(os.environ, {TESTLDAP_ENV: confdir}),
                mock.patch('os.kill') as kill,
            ):
                slapd.tearDown()
        kill.assert_called_once_with(4711, 15)

    def test_ldif_teardown_reports_failing_registry_pop(self):
        ldif = testing.Ldif(
            testing.resource('ldifs/base.ldif'), bases=(), name='TestLdif'
        )
        error = ValueError('popGlobalRegistry() called out of sync')
        # ``subprocess.call`` is mocked to keep ``ldapdelete`` away from the
        # LDAP server of other tests.
        with (
            tempfile.TemporaryDirectory() as confdir,
            mock.patch.dict(os.environ, {TESTLDAP_ENV: confdir}),
            mock.patch('subprocess.call', return_value=0),
            mock.patch.object(zca, 'popGlobalRegistry', side_effect=error),
            redirect_stdout(io.StringIO()) as stdout,
        ):
            ldif.tearDown()
        output = stdout.getvalue()
        self.assertIn('pop global registry failed', output)
        self.assertIn(str(error), output)

    def test_ldif_without_ldifs(self):
        self.assertEqual(testing.Ldif(bases=(), name='TestLdif').ldifs, ())
        self.assertEqual(
            testing.Ldif('a.ldif', bases=(), name='TestLdif').ldifs, ('a.ldif',)
        )
        self.assertEqual(
            testing.Ldif(('a.ldif', 'b.ldif'), bases=(), name='TestLdif').ldifs,
            ('a.ldif', 'b.ldif'),
        )
