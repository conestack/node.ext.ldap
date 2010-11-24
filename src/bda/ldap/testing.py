import os
import shutil
import subprocess
import tempfile
import time
from plone.testing import Layer
from pkg_resources import resource_filename
from bda.ldap import (
    ONELEVEL,
    SUBTREE,
    LDAPProps,
)
from bda.ldap.users import (
    LDAPUsersConfig,
    LDAPGroupsConfig,
)

SCHEMA = os.environ.get('SCHEMA')
try:
    SLAPDBIN = os.environ['SLAPD_BIN']
    SLAPDURIS = os.environ['SLAPD_URIS']
    LDAPADDBIN = os.environ['LDAP_ADD_BIN']
    LDAPDELETEBIN = os.environ['LDAP_DELETE_BIN']
except KeyError:
    raise RuntimeError("Environment variables SLAPD_BIN,"
            " SLAPD_URIS, LDAP_ADD_BIN, LDAP_DELETE_BIN needed.")

def resource(string):
    return resource_filename(__name__, 'tests/'+string)

def read_env(layer):
    if layer.get('confdir', None) is not None:
        return
    tmpdir = os.environ.get('bda.ldap.testldap.env', None)
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        layer['externalpidfile'] = False
    else:
        layer['externalpidfile'] = True
    layer['confdir'] = tmpdir
    layer['dbdir'] = "%s/openldap-data" % (layer['confdir'],)
    layer['slapdconf'] = "%s/slapd.conf" % (layer['confdir'],)
    layer['binddn'] = "cn=Manager,dc=my-domain,dc=com"
    layer['bindpw'] = "secret"

slapdconf_template = """\
%(schema)s

pidfile		%(confdir)s/slapd.pid
argsfile	%(confdir)s/slapd.args

database	bdb
suffix		"dc=my-domain,dc=com"
rootdn		"%(binddn)s"
rootpw		%(bindpw)s
directory	%(dbdir)s
# Indices to maintain
index	objectClass	eq
"""

class SlapdConf(Layer):
    """generate slapd.conf
    """
    def __init__(self, schema):
        """
        ``schema``: List of paths to our schema files
        """
        super(SlapdConf, self).__init__()
        self.schema = schema

    def setUp(self):
        """take a template, replace, write slapd.conf store path for others to
        knows
        """
        read_env(self)
        binddn = self['binddn']
        bindpw = self['bindpw']
        confdir = self['confdir']
        dbdir = self['dbdir']
        slapdconf = self['slapdconf']
        schema = '\n'.join(
                ["include %s" % (schema,) for schema in self.schema]
                )
        # generate config file
        with open(slapdconf, 'w') as slapdconf:
            slapdconf.write(slapdconf_template % dict(
                binddn=binddn,
                bindpw=bindpw,
                confdir=confdir,
                dbdir=dbdir,
                schema=schema
                ))
        os.mkdir(dbdir)
        self['props'] = props
        print "SlapdConf set up."

    def tearDown(self):
        """remove our traces
        """
        read_env(self)
        shutil.rmtree(self['confdir'])
        print "SlapdConf torn down."

schema = (
        resource('schema/core.schema'),
        resource('schema/cosine.schema'),
        resource('schema/inetorgperson.schema'),
        )
SLAPD_CONF = SlapdConf(schema)

class LDAPLayer(Layer):
    """Base class for ldap layers to _subclass_ from
    """
    defaultBases = (SLAPD_CONF,)

    def __init__(self, uris=SLAPDURIS, **kws):
        super(LDAPLayer, self).__init__(**kws)
        self['uris'] = uris

class Slapd(LDAPLayer):
    """Start/Stop an LDAP Server
    """
    def __init__(self, slapdbin=SLAPDBIN, **kws):
        super(Slapd, self).__init__(**kws)
        self.slapdbin = slapdbin
        self.slapd = None

    def setUp(self):
        """start slapd
        """
        print "\nStarting LDAP server: ",
        read_env(self)
        cmd = [self.slapdbin, '-f', self['slapdconf'], '-h', self['uris'],
                '-d', '0']
        self.slapd = subprocess.Popen(cmd)
        time.sleep(1)
        print "done."

    def tearDown(self):
        """stop the previously started slapd
        """
        print "\nStopping LDAP Server: ",
        read_env(self)
        if self['externalpidfile']:
            with open(os.path.join(self['confdir'], 'slapd.pid')) as pidfile:
                pid = int(pidfile.read())
        else:
            pid = self.slapd.pid
        os.kill(pid, 15)
        if self.slapd is not None:
            print "waiting for slapd to terminate...",
            self.slapd.wait()
        print "done."
        print "Whiping ldap data directory %s: " % (self['dbdir'],),
        for file in os.listdir(self['dbdir']):
            os.remove('%s/%s' % (self['dbdir'], file))
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
            ucfg=None,
            **kws):
        super(Ldif, self).__init__(**kws)
        self.ldapaddbin = ldapaddbin
        self.ldapdeletebin = ldapdeletebin
        self.ldifs = type(ldifs) is tuple and ldifs or (ldifs,)
        #self['ucfg'] = ucfg
        self.ucfg = ucfg

    def setUp(self):
        """run ldapadd for list of ldifs
        """
        read_env(self)
        self['ucfg'] = self.ucfg
        print
        for ldif in self.ldifs:
            print "Adding ldif %s: " % (ldif,),
            cmd = [self.ldapaddbin, '-f', ldif, '-x', '-D', self['binddn'], '-w',
                    self['bindpw'], '-c', '-a', '-H', self['uris']]
            retcode = subprocess.call(cmd)
            print "done."

    def tearDown(self):
        """remove previously added ldifs
        """
        print
        read_env(self)
        for ldif in self.ldifs:
            print "Removing ldif %s recursively: " % (ldif,),
            with open(ldif) as ldif:
                dns = [x.strip().split(' ',1)[1]  for x in ldif if
                        x.startswith('dn: ')]
            cmd = [self.ldapdeletebin, '-x', '-D', self['binddn'], '-c', '-r',
                    '-w', self['bindpw'], '-H', self['uris']] + dns
            retcode = subprocess.call(cmd, stderr=subprocess.PIPE)
            print "done."
        try:
            del self['ucfg']
        except KeyError:
            pass

# testing ldap props
user = 'cn=Manager,dc=my-domain,dc=com'
pwd = 'secret'
# old: props = LDAPProps('127.0.0.1', 12345, user, pwd, cache=False)
props = LDAPProps(
        uri='ldap://127.0.0.1:12345/',
        user=user,
        password=pwd,
        cache=False,
        )

# base users config
ucfg = LDAPUsersConfig(
        baseDN='dc=my-domain,dc=com',
        attrmap={
            'id': 'sn',
            'login': 'description',
            'telephoneNumber': 'telephoneNumber',
            'rdn': 'ou',
            'sn': 'sn',
            },
        scope=SUBTREE,
        queryFilter='(objectClass=person)',
        )

# users config for 300-users data.
ucfg300 = LDAPUsersConfig(
        baseDN='ou=users300,dc=my-domain,dc=com',
        attrmap={
            'id': 'uid',
            'login': 'uid',
            'cn': 'cn',
            'rdn': 'uid',
            'sn': 'sn',
            'mail': 'mail',
            },
        scope=ONELEVEL,
        queryFilter='(objectClass=inetOrgPerson)',
        )

# users config for 700-users data.
ucfg700 = LDAPUsersConfig(
        baseDN='ou=users700,dc=my-domain,dc=com',
        attrmap={
            'id': 'uid',
            'login': 'uid',
            'cn': 'cn',
            'rdn': 'uid',
            'sn': 'sn',
            'mail': 'mail',
            },
        scope=ONELEVEL,
        queryFilter='(objectClass=inetOrgPerson)',
        )

# users config for 1000-users data.
ucfg1000 = LDAPUsersConfig(
        baseDN='ou=users1000,dc=my-domain,dc=com',
        attrmap={
            'id': 'uid',
            'login': 'uid',
            'cn': 'cn',
            'rdn': 'uid',
            'sn': 'sn',
            'mail': 'mail',
            },
        scope=ONELEVEL,
        queryFilter='(objectClass=inetOrgPerson)',
        )

# users config for 2000-users data.
ucfg2000 = LDAPUsersConfig(
        baseDN='ou=users2000,dc=my-domain,dc=com',
        attrmap={
            'id': 'uid',
            'login': 'uid',
            'cn': 'cn',
            'rdn': 'uid',
            'sn': 'sn',
            'mail': 'mail',
            },
        scope=ONELEVEL,
        queryFilter='(objectClass=inetOrgPerson)',
        )

# base groups config
#gcfg_openldap = LDAPGroupsConfig(
#        baseDN='dc=my-domain,dc=com',
#        id_attr='cn',
#        scope=SUBTREE,
#        queryFilter='(objectClass=groupOfNames)',
#        member_relation='member:dn',
#        )

# old ones used by current bda.ldap tests - 2010-11-09
LDIF_data = Ldif(
        resource('ldifs/data.ldif'),
        name='LDIF_data',
        ucfg=ucfg,
        )
LDIF_principals = Ldif(
        resource('ldifs/principals.ldif'),
        bases=(LDIF_data,),
        name='LDIF_principals',
        ucfg=ucfg,
        )

LDIF_data_old_props = Ldif(
        resource('ldifs/data.ldif'),
        name='LDIF_data',
        ucfg=ucfg,
        )
LDIF_principals_old_props = Ldif(
        resource('ldifs/principals.ldif'),
        bases=(LDIF_data,),
        name='LDIF_principals',
        ucfg=ucfg,
        )

# new ones
LDIF_base = Ldif(resource('ldifs/base.ldif'))
LDIF_users300 = Ldif(
        resource('ldifs/users300.ldif'),
        bases=(LDIF_base,),
        name="LDIF_users300",
        ucfg=ucfg300,
        )
LDIF_users700 = Ldif(
        resource('ldifs/users700.ldif'),
        bases=(LDIF_base,),
        name="LDIF_users700",
        ucfg=ucfg700,
        )
LDIF_users1000 = Ldif(
        resource('ldifs/users1000.ldif'),
        bases=(LDIF_base,),
        name="LDIF_users1000",
        ucfg=ucfg1000,
        )
LDIF_users2000 = Ldif(
        resource('ldifs/users2000.ldif'),
        bases=(LDIF_base,),
        name="LDIF_users2000",
        ucfg=ucfg2000,
        )
