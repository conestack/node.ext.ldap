from node.ext.ldap import main
from node.tests import NodeTestCase
from unittest import mock
import importlib
import os
import sys
import tempfile


class Layer:
    def __init__(self, name, *bases):
        self.__name__ = name
        self.__bases__ = bases
        self.setUp = mock.Mock()
        self.tearDown = mock.Mock()


class TestMain(NodeTestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.environ = mock.patch.dict(os.environ, {'HOME': self.home.name})
        self.environ.start()

    def tearDown(self):
        self.environ.stop()
        self.home.cleanup()

    def test_paths(self):
        self.assertEqual(main.user_home(), self.home.name)
        self.assertEqual(
            main.env_path(),
            os.path.join(self.home.name, '.node.ext.ldap.testldap.env'),
        )
        self.assertEqual(
            main.ldif_path(),
            os.path.join(self.home.name, '.node.ext.ldap.testldap.ldif'),
        )

    def test_env_files(self):
        self.assertIsNone(main.read_tmp())
        self.assertIsNone(main.read_ldif())
        tmpfolder = main.mk_tmp()
        main.mk_ldif('base')
        try:
            self.assertEqual(main.read_tmp(), tmpfolder)
            self.assertEqual(main.read_ldif(), 'base')
        finally:
            os.rmdir(tmpfolder)
        main.cleanup_env()
        self.assertFalse(os.path.exists(main.env_path()))
        self.assertFalse(os.path.exists(main.ldif_path()))

    def test_flatlayers(self):
        base = Layer('base')
        child = Layer('child', base)
        self.assertEqual(main.flatlayers(child), [base, child])
        self.assertEqual(main.flatlayers(base), [base])

    def test_startslapd_and_stopslapd(self):
        base = Layer('base')
        child = Layer('child', base)
        calls = mock.Mock()
        calls.attach_mock(base.setUp, 'base_setUp')
        calls.attach_mock(child.setUp, 'child_setUp')
        calls.attach_mock(base.tearDown, 'base_tearDown')
        calls.attach_mock(child.tearDown, 'child_tearDown')
        with mock.patch.dict(main.testing.ldif_layer, {'child': child}):
            main.startslapd(child, 'child')
            tmpfolder = os.environ['node.ext.ldap.testldap.env']
            self.assertEqual(main.read_tmp(), tmpfolder)
            self.assertEqual(main.read_ldif(), 'child')
            self.assertEqual(os.environ['node.ext.ldap.testldap.skip_zca_hook'], 'skip')
            main.stopslapd()
        os.rmdir(tmpfolder)
        self.assertEqual(
            calls.mock_calls,
            [
                mock.call.base_setUp(),
                mock.call.child_setUp(),
                mock.call.child_tearDown(),
                mock.call.base_tearDown(),
            ],
        )
        self.assertFalse(os.path.exists(main.env_path()))

    def test_slapd_start(self):
        with (
            mock.patch.object(sys, 'argv', ['testldap', 'start', 'base']),
            mock.patch('subprocess.call', return_value=1),
            mock.patch.object(main, 'startslapd') as startslapd,
        ):
            main.slapd()
        startslapd.assert_called_once_with(main.testing.ldif_layer['base'], 'base')

    def test_slapd_start_already_running(self):
        with (
            mock.patch.object(sys, 'argv', ['testldap', 'start']),
            mock.patch('subprocess.call', return_value=0),
            mock.patch.object(main, 'startslapd') as startslapd,
            mock.patch('builtins.print') as print_,
        ):
            with self.assertRaises(SystemExit) as arc:
                main.slapd()
        self.assertEqual(arc.exception.code, 2)
        print_.assert_called_once_with('LDAP already running. abort.')
        startslapd.assert_not_called()

    def test_slapd_stop(self):
        with (
            mock.patch.object(sys, 'argv', ['testldap', 'stop']),
            mock.patch.object(main, 'stopslapd') as stopslapd,
        ):
            main.slapd()
        stopslapd.assert_called_once_with()

    def test_additional_ldif_layers(self):
        try:
            with (
                mock.patch.dict(os.environ, {'ADDITIONAL_LDIF_LAYERS': ' json  os '}),
                mock.patch('importlib.import_module') as import_module,
            ):
                importlib.reload(main)
            self.assertEqual(
                import_module.mock_calls, [mock.call('json'), mock.call('os')]
            )
        finally:
            importlib.reload(main)
