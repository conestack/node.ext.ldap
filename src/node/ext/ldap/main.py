import os
import sys
import tempfile
from bda.ldap import testing

def user_home():
    # XXX: unix only ATM
    return os.getenv('HOME')

def env_path():
    return os.path.join(user_home(), '.bda.ldap.testldap.env')

def ldif_path():
    return os.path.join(user_home(), '.bda.ldap.testldap.ldif')

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

def startslapd(layer, args):
    mk_ldif(args[0])
    os.environ['bda.ldap.testldap.env'] = mk_tmp()
    for base in layer.defaultBases + layer.__bases__:
        for subbase in base.defaultBases:
            subbase.setUp()
        base.setUp()
    layer.setUp()

def stopslapd(layer, args):
    os.environ['bda.ldap.testldap.env'] = read_tmp()
    layer.tearDown()
    for base in layer.defaultBases:
        base.tearDown()
        for subbase in base.defaultBases:
            subbase.tearDown()
    cleanup_env()

CMD = {
    'start': startslapd,
    'stop': stopslapd,
}

def slapd():
    args = sys.argv[1:]
    if (len(args) == 0) \
      or (len(args) == 1 and args[0] != 'stop') \
      or (len(args) == 2 and args[1] != 'start') \
      or (len(args) > 2):
        print u"Usage: ./bin/testldap [LDIFLayer] start|stop"
        print u"'start' option requires 'LDIFLayer'"
        sys.exit(2)
    if len(args) == 1:
        ldif = read_ldif()
        if not ldif:
            print u"Server not Running"
            sys.exit(2)
        cmd = args[0]
    else:
        if read_tmp() is not None:
            print u"LDAP already running. abort."
            sys.exit(2)
        ldif = args[0]
        cmd = args[1]
    try:
        layer = getattr(testing, ldif)
    except AttributeError:
        print u"Given layer not found: %s" % args[0]
        sys.exit(2)
    CMD[cmd](layer, args)