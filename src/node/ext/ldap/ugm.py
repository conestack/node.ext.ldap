from node.base import AbstractNode
from zope.interface import implements

from node.ext.ldap.bbb import LDAPNode
from node.ext.ldap.debug import debug
from node.ext.ldap.interfaces import ILDAPGroupsConfig as IGroupsConfig
from node.ext.ldap.interfaces import ILDAPUsersConfig as IUsersConfig
from node.ext.ldap.properties import LDAPProps
from node.ext.ldap.scope import ONELEVEL
from node.ext.ldap.outbox import Group as _Group
from node.ext.ldap.outbox import Principals as _Principals
from node.ext.ldap.outbox import User as _User


class PrincipalsConfig(object):
    """Superclass for UsersConfig and GroupsConfig
    """
    def __init__(self,
            baseDN='',
            newDN='',
            attrmap={},
            scope=ONELEVEL,
            queryFilter='',
            objectClasses=[],
            member_relation=''):
        self.baseDN = baseDN
        self.newDN = newDN or baseDN
        self.attrmap = attrmap
        self.scope = scope
        self.queryFilter = queryFilter
        self.objectClasses = objectClasses
        self.member_relation = member_relation


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
        self.context._seckey_attrs = ('dn',)
        if cfg.member_relation:
            self.context._child_relation = cfg.member_relation

    def idbydn(self, dn):
        """return a principals id for a given dn

        raise KeyError if not enlisted
        """
        self.context.keys()
        return self.context._seckeys['dn'][dn]


class _UserGroups(AbstractNode):
    """did I mention dynamic plumbing?

    return only groups the user is a member of
    """
    def __init__(self, context, user):
        self.context = context
        self.user = user

    def __contains__(self, key):
        for id, group in self.context.iteritems():
            if key == id:
                if self.user.id in group:
                    return True
        return False

    def __delitem__(self, key):
        del self.context[key][self.user.id]

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return self.context[key]

    def __iter__(self):
        for id, group in self.context.iteritems():
            if self.user.id in group:
                yield id

    def add(self, group_or_id):
        try:
            group_id = group_or_id.id
        except AttributeError:
            group_id = group_or_id
        self.context[group_id].add(self.user)

    def search(self, attrlist=None):
        if not attrlist:
            return self.keys()
        # XXX: nasty, the flattened attrs are turned into lists again
        return [(id, dict([(x, [self[id].context.attrs[x]]) for x in attrlist])) for id in self]


class User(_User):
    """User that knows to fetch group info from ldap

    XXX: feels like dynamic plumbing and no specific class here or
    maybe static plumbing
    """
    @property
    def groups(self):
        """A filtered view of all groups
        """
        return _UserGroups(self.__parent__.groups, user=self)


class Users(Principals):
    """Manage LDAP users
    """
    principal_factory = User

    def __init__(self, props, cfg):
        super(Users, self).__init__(props, cfg)
        if cfg.attrmap['login'] != cfg.attrmap['id']:
            self.context._seckey_attrs += (cfg.attrmap['login'],)

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


class Group(_Group):
    """Some ldap specifics for groups
    """
    def __init__(self, *args, **kw):
        super(Group, self).__init__(*args, **kw)
        self._keys = None

    # XXX: HACK
    @property
    def _member_attr(self):
        return self.__parent__._member_attr

    @property
    def _memberdns(self):
        # XXX: multi-valued attrs should always be lists
        members = self.context.attrs[self._member_attr]
        if type(members) not in (list, tuple):
            members = [members,]
        return list(members)

    def __contains__(self, key):
        for id in self:
            if key == id:
                return True
        return False

    def __delitem__(self, key):
        if key not in self:
            raise KeyError(key)
        dn = self.__parent__.users.context.child_dn(key)
        members = self._memberdns
        members.remove(dn)
        self.context.attrs[self._member_attr] = members
        self.context()

    def __getitem__(self, key):
        # XXX: only users for now, we are not parent
        if key not in self:
            raise KeyError(key)
        return self.__parent__.users[key]

    def __iter__(self):
        for dn in self._memberdns:
            if dn == "cn=nobody":
                continue
            # XXX for now we only check in the users folder
            try:
                yield self.__parent__.users.idbydn(dn)
            except KeyError:
                print "Ignoring '%s' as a member of '%s'" % (dn, self.id)

    def add(self, principal_or_id, error_if_present=True):
        """modeled after set.add() + raise flag

        XXX: setitem felt wrong for adding a principal as the key
        cannot be specified
        """
        try:
            principal_id = principal_or_id.id
        except AttributeError:
            principal_id = principal_or_id
        if principal_id in self:
            if error_if_present:
                raise ValueError("Already a member: '%s'." % (principal_id,))
            return
        dn = self.__parent__.users.context.child_dn(principal_id)
        self.context.attrs[self._member_attr] = self._memberdns + [dn]
        self.context()

    def search(self, attrlist=None):
        """XXX: incomplete signature

        XXX: unalias attrs

        XXX: really implement it
        """
        if not attrlist:
            return self.keys()
        # XXX: nasty, the flattened attrs are turned into lists again
        return [(id, dict([(x, [self[id].context.attrs[x]]) for x in attrlist])) for id in self]


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

    def __init__(self, props, cfg):
        super(Groups, self).__init__(props, cfg)
        if 'groupOfNames' in cfg.objectClasses:
            self._member_attr = 'member'
        elif 'groupOfUniqueNames' in cfg.objectClasses:
            self._member_attr = 'uniqueMember'
        else:
            raise ValueError('Unsupported groups: %s' % (cfg.objectClasses,))

    def __setitem__(self, key, vessel):
        vessel.attrs.setdefault(self._member_attr, []).insert(0, 'cn=nobody')
        super(Groups, self).__setitem__(key, vessel)
