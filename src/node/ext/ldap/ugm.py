from zope.interface import implements

from node.ext.ldap.bbb import LDAPNode
from node.ext.ldap.debug import debug
from node.ext.ldap.interfaces import ILDAPGroupsConfig as IGroupsConfig
from node.ext.ldap.interfaces import ILDAPUsersConfig as IUsersConfig
from node.ext.ldap.properties import LDAPProps
from node.ext.ldap.scope import ONELEVEL
from node.ext.ldap.outbox import Group
from node.ext.ldap.outbox import Principals as _Principals
from node.ext.ldap.outbox import User


class PrincipalsConfig(object):
    """Superclass for UsersConfig and GroupsConfig
    """
    def __init__(self,
            baseDN='',
            attrmap={},
            scope=ONELEVEL,
            queryFilter='',
            objectClasses=[]):
        self.baseDN = baseDN
        self.attrmap = attrmap
        self.scope = scope
        self.queryFilter = queryFilter
        self.objectClasses = objectClasses


class UsersConfig(PrincipalsConfig):
    """Define how users look and where they are
    """
    implements(IUsersConfig)


class GroupsConfig(PrincipalsConfig):
    """Define how groups look and where they are
    """
    implements(IGroupsConfig)


class Principals(_Principals):
    """Superclass for Users and Groups
    """
    def __init__(self, props, cfg):
        context = LDAPNode(name=cfg.baseDN, props=props)
        super(Principals, self).__init__(context, cfg.attrmap)
        self.context._child_filter = cfg.queryFilter
        self.context._child_scope = int(cfg.scope)
        self.context._child_objectClasses = cfg.objectClasses
        self.context._key_attr = cfg.attrmap['id']
        self.context._rdn_attr = cfg.attrmap['rdn']


class Users(Principals):
    """Manage LDAP users
    """
    principal_factory = User

    def __init__(self, props, cfg):
        super(Users, self).__init__(props, cfg)
        if cfg.attrmap['login'] != cfg.attrmap['id']:
            self.context._seckey_attrs = (cfg.attrmap['login'],)

    # XXX: do we really need this?
    # XXX: login is a mapped attr, we could simply search on it
    def idbylogin(self, login):
        """Return the users id or raise KeyError
        """
        self.context.keys()
        if self.principal_attrmap['login'] == self.principal_attrmap['id']:
            if login not in self:
                raise KeyError(login)
            # XXX: Is this sane, or should we tell that they are the same?
            return login
        return self.context._seckeys[self.principal_attrmap['login']][login]

    @debug(['authentication'])
    def authenticate(self, login=None, pw=None, id=None):
        """Authenticate a user either by id xor by login

        If successful, the user's id is returned, otherwise None
        """
        if id is not None and login is not None:
            raise ValueError(u"Either specify id or login, not both.")
        if pw is None:
            raise ValueError(u"You need to specify a password")
        if login:
            try:
                id = self.idbylogin(login)
            except KeyError:
                return None
        try:
            userdn = self.context.child_dn(id)
        except KeyError:
            return None
        return self.context._session.authenticate(userdn, pw) and id or None

    @debug(['authentication'])
    def passwd(self, id, oldpw, newpw):
        """Change a users password
        """
        self.context._session.passwd(self.context.child_dn(id), oldpw, newpw)


class Groups(Principals):
    """Manage LDAP groups

    XXX
        for groups children are found by:
        - we have a multivalue attribute pointing to member dns
        - has an attribute pointing to our dn
        - we have an attribute that matches another attribute on the user

        AD: dn:memberOf
        openldap: member:dn
        posix: memberUid:uidNumber|gidNumber:gidNumber
        arbitrary: group_attr:user_attr  |   &    ()
    """
    principal_factory = Group
