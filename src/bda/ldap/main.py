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
    args = sys.argv[1:]
    if len(args) != 2:
        print u"Usage: ./bin/testldap LDIFLayer start|stop"
        sys.exit(2)
    layer = getattr(testing, args[0])
    if not layer:
        print u"Given layer not found: %s" % args[0]
        sys.exit(2)
    cmd = args[1]
    if not cmd in CMD.keys():
        print u"Unknown command: %s" % cmd
    CMD[cmd](layer)