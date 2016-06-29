# -*- coding: utf-8 -*-
from importlib import import_module
from node.ext.ldap import testing
import argparse
import os
import subprocess
import sys
import tempfile


# additional LDIF layer containing modules
additional_layers = os.environ.get('ADDITIONAL_LDIF_LAYERS')
if additional_layers:
    modules = [_.strip() for _ in additional_layers.split(' ') if _.strip()]
    for mod in modules:
        import_module(mod)


parser = argparse.ArgumentParser(
    description='Controls test LDAP server, loads predefined LDIF.'
)
parser.add_argument(
    'task',
    nargs=1,
    action='store',
    choices=['start', 'stop'],
    help='start or stop LDAP server'
)
parser.add_argument(
    'ldiflayer',
    nargs='?',
    default='base',
    choices=testing.ldif_layer.keys(),
    help='Predefined LDIF Layer to load.'
)


# XXX: could these go into parts/testldap?
def user_home():
    # XXX: unix only ATM
    return os.getenv('HOME')


def env_path():
    return os.path.join(user_home(), '.node.ext.ldap.testldap.env')


def ldif_path():
    return os.path.join(user_home(), '.node.ext.ldap.testldap.ldif')


def mk_tmp():
    tmpfolder = tempfile.mkdtemp()
    with open(env_path(), 'w') as file:
        file.write(tmpfolder)
    return tmpfolder


def mk_ldif(ldif):
    with open(ldif_path(), 'w') as file:
        file.write(ldif)


def _read_file(path):
    try:
        with open(path, 'r') as file:
            ret = file.read()
        return ret
    except IOError:
        return None


def read_tmp():
    return _read_file(env_path())


def read_ldif():
    return _read_file(ldif_path())


def cleanup_env():
    os.remove(env_path())
    os.remove(ldif_path())


def flatlayers(layer, layers=[]):
    layers.insert(0, layer)
    for base in layer.__bases__:
        flatlayers(base, layers)
    return layers


def startslapd(layer, layername):
    mk_ldif(layername)
    os.environ['node.ext.ldap.testldap.env'] = mk_tmp()
    os.environ['node.ext.ldap.testldap.skip_zca_hook'] = 'skip'
    for layer in flatlayers(layer):
        layer.setUp()


def stopslapd():
    layer = testing.ldif_layer[read_ldif()]
    os.environ['node.ext.ldap.testldap.env'] = read_tmp()
    os.environ['node.ext.ldap.testldap.skip_zca_hook'] = 'skip'
    for layer in reversed(flatlayers(layer)):
        layer.tearDown()
    cleanup_env()


def slapd():
    ns = parser.parse_args()
    task = ns.task[0]
    layer = testing.ldif_layer[ns.ldiflayer]
    if task == 'start':
        # XXX should check for distinct slapd
        checkslapd = 'ps ax| grep slapd| grep -v grep -q'
        if not subprocess.call(checkslapd, shell=True) == 1:
            print u"LDAP already running. abort."
            sys.exit(2)
        startslapd(layer, ns.ldiflayer)
    else:
        stopslapd()
