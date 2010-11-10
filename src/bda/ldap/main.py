import sys
from bda.ldap import testing

def startslapd(layer):
    for base in layer.defaultBases:
        base.setUp()
    leyer.setUp()

def stopslapd(layer):
    layer.tearDown()
    for base in layer.defaultBases:
        base.tearDown()

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