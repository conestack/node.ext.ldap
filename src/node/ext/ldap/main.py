import os
import subprocess
import sys
import tempfile
from node.ext.ldap import testing


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


def startslapd(layer, args):
    mk_ldif(args[1])
    os.environ['node.ext.ldap.testldap.env'] = mk_tmp()
    for layer in flatlayers(layer):
        layer.setUp(args[2:])


def stopslapd(layer, args):
    os.environ['node.ext.ldap.testldap.env'] = read_tmp()
    for layer in reversed(flatlayers(layer)):
        layer.tearDown()
    cleanup_env()


CMD = {
    'start': startslapd,
    'stop': stopslapd,
}

def slapd():
    args = sys.argv[1:]
    if (len(args) == 0) \
      or (len(args) == 1 and args[0] != 'stop') \
      or (len(args) >= 2 and args[0] != 'start'):
        print
        print u"Usage: ./bin/testldap start|stop [LDIFLayer]"
        print u"'start' option requires 'LDIFLayer'"
        print u"Available layers:"
        for x in sorted([x[5:] for x in dir(testing) if x.startswith('LDIF_')]):
            print "\t" + x
        sys.exit(2)
    if len(args) == 1:
        ldif = read_ldif()
        if not ldif:
            print u"Server not Running"
            sys.exit(2)
        cmd = args[0]
    else:
        if read_tmp() is not None:
            checkslapd = 'ps ax| grep slapd| grep -v grep -q'
            if not subprocess.call(checkslapd, shell=True) == 1:
                print u"LDAP already running. abort."
                sys.exit(2)
        cmd = args[0]
        ldif = args[1]
    try:
        layer = getattr(testing, 'LDIF_%s' % ldif)
    except AttributeError:
        print u"Given layer not found: %s" % args[0]
        sys.exit(2)
    CMD[cmd](layer, args)