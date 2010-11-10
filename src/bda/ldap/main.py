import os
import sys
import tempfile
from bda.ldap import testing

def confpath():
    return os.path.join(os.getenv('HOME'), '.bda.ldap.testldap.env')

def dump():
    tmpfolder = tempfile.mkdtemp()
    with open(confpath(), 'w') as file:
        file.write(tmpfolder)

def read():
    with open(confpath(), 'r') as file:
        ret = file.read()
    return ret

def delete():
    os.remove(confpath())

def startslapd(layer):
    dump()
    os.environ['bda.ldap.testldap.env'] = read()
    for base in layer.defaultBases:
        for subbase in base.defaultBases:
            subbase.setUp()
        base.setUp()
    layer.setUp()

def stopslapd(layer):
    os.environ['bda.ldap.testldap.env'] = read()
    layer.tearDown()
    for base in layer.defaultBases:
        base.tearDown()
        for subbase in base.defaultBases:
            subbase.tearDown()
    delete()

CMD = {
    'start': startslapd,
    'stop': stopslapd,
}

def slapd():
    #import os
    #print os.environ['SLAPD_BIN']
    #print os.environ['SLAPD_URIS']
    #print os.environ['LDAP_DELETE_BIN']
    #print os.environ['LDAP_ADD_BIN']
    #return
    args = sys.argv[1:]
    if len(args) != 2:
        print u"Usage: ./bin/testldap LDIFLayer start|stop"
        sys.exit(2)
    try:
        layer = getattr(testing, args[0])
    except AttributeError:
        print u"Given layer not found: %s" % args[0]
        sys.exit(2)
    cmd = args[1]
    if not cmd in CMD.keys():
        print u"Unknown command: %s" % cmd
        sys.exit(2)
    CMD[cmd](layer)