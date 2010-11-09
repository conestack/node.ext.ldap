from bda.ldap import LDAPProps
from bda.ldap.users import LDAPUsersConfig
from bda.ldap.users import LDAPGroupsConfig
from bda.ldap import SUBTREE

user = 'cn=Manager,dc=my-domain,dc=com'
pwd = 'secret'
props = LDAPProps('127.0.0.1', 12345, user, pwd, cache=False)
ucfg = LDAPUsersConfig(
        baseDN='dc=my-domain,dc=com',
        attrmap={
            'id': 'sn',
            'login': 'cn',
            },
        scope=SUBTREE,
        queryFilter='(objectClass=person)',
        )
#gcfg_openldap = LDAPGroupsConfig(
#        props,
#        baseDN='dc=my-domain,dc=com',
#        id_attr='cn',
#        scope=SUBTREE,
#        queryFilter='(objectClass=groupOfNames)',
#        member_relation='member:dn',
#        )

# === the new stuff ============

import os
import subprocess
import time

from plone.testing import Layer
from pkg_resources import resource_filename


def resource(string):
    return resource_filename(__name__, 'tests/'+string)


try:
    SLAPDBIN = os.environ['SLAPD_BIN']
    SLAPDCONF = os.environ['SLAPD_CONF']
    SLAPDURIS = os.environ['SLAPD_URIS']
    LDAPADDBIN = os.environ['LDAP_ADD_BIN']
    LDAPDELETEBIN = os.environ['LDAP_DELETE_BIN']
except KeyError:
    raise RuntimeError("Environment variables SLAPD_BIN, SLAPD_CONF,"
            " SLAPD_URIS, LDAP_ADD_BIN, LDAP_DELETE_BIN needed.")


class LDAPLayer(Layer):
    """Base class for ldap layers to _subclass_ from
    """
    def __init__(self, slapdconf=SLAPDCONF, uris=SLAPDURIS, **kws):
        super(LDAPLayer, self).__init__(**kws)
        self.slapdconf = slapdconf
        self.uris = uris
        with open(slapdconf) as slapdconf:
            data = dict([x.strip().split() for x in slapdconf if x[:6] in
                ('direct', 'rootdn', 'rootpw')])
        self.dbdir = data['directory']
        self.binddn = data['rootdn'].split('"')[1]
        self.bindpw = data['rootpw']


class Slapd(LDAPLayer):
    """Start/Stop an LDAP Server
    """
    def __init__(self, slapdbin=SLAPDBIN, **kws):
        super(Slapd, self).__init__(**kws)
        self.slapdbin = slapdbin

    def setUp(self):
        """start slapd
        """
        print "\nStarting LDAP server: ",
        self.slapd = subprocess.Popen(
                [self.slapdbin, '-f', self.slapdconf, '-h', self.uris,
                    '-d', '0']
                )
        time.sleep(1)
        print "done."

    def tearDown(self):
        """stop the previously started slapd
        """
        print "\nStopping LDAP Server: ",
        os.kill(self.slapd.pid, 15)
        print "waiting for slapd to terminate...",
        self.slapd.wait()
        print "done."
        print "Whiping ldap data directory %s: " % (self.dbdir,),
        for file in os.listdir(self.dbdir):
            os.remove('%s/%s' % (self.dbdir, file))
        print "done."

SLAPD = Slapd()


class Ldif(LDAPLayer):
    """Adds/removes ldif data to/from a server
    """
    defaultBases = (SLAPD,)

    def __init__(self,
            ldifs=tuple(),
            ldapaddbin=LDAPADDBIN,
            ldapdeletebin=LDAPDELETEBIN,
            **kws):
        super(Ldif, self).__init__(**kws)
        self.ldapaddbin = ldapaddbin
        self.ldapdeletebin = ldapdeletebin
        self.ldifs = type(ldifs) is tuple and ldifs or (ldifs,)

    def setUp(self):
        """run ldapadd for list of ldifs
        """
        print
        for ldif in self.ldifs:
            print "Adding ldif %s: " % (ldif,),
            cmd = [self.ldapaddbin, '-f', ldif, '-x', '-D', self.binddn, '-w',
                    self.bindpw, '-c', '-a', '-H', self.uris]
            retcode = subprocess.call(cmd)
            print "done."

    def tearDown(self):
        """remove previously added ldifs
        """
        print
        for ldif in self.ldifs:
            print "Removing ldif %s recursively: " % (ldif,),
            with open(ldif) as ldif:
                dns = [x.strip().split(' ',1)[1]  for x in ldif if
                        x.startswith('dn: ')]
            cmd = [self.ldapdeletebin, '-x', '-D', self.binddn, '-c', '-r',
                    '-w', self.bindpw, '-H', self.uris] + dns
            retcode = subprocess.call(cmd, stderr=subprocess.PIPE)
            print "done."


# old ones used by current bda.ldap tests - 2010-11-09
LDIF_data = Ldif(
        resource('ldifs/data.ldif'),
        name='LDIF_data',
        )
LDIF_principals = Ldif(
        resource('ldifs/principals.ldif'),
        bases=(LDIF_data,),
        name='LDIF_principals',
        )

# new ones
LDIF_base = Ldif(resource('ldifs/base.ldif'))
LDIF_users300 = Ldif(
        resource('ldifs/users300.ldif'),
        bases=(LDIF_base,),
        name="LDIF_users300",
        )
LDIF_users700 = Ldif(
        resource('ldifs/users700.ldif'),
        bases=(LDIF_base,),
        name="LDIF_users700",
        )
LDIF_users1000 = Ldif(
        resource('ldifs/users1000.ldif'),
        bases=(LDIF_base,),
        name="LDIF_users1000",
        )
LDIF_users1000 = Ldif(
        resource('ldifs/users2000.ldif'),
        bases=(LDIF_base,),
        name="LDIF_users2000",
        )
