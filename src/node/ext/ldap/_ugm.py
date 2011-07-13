from plumber import (
    plumber,
    default,
    extend,
    finalize,
    Part,
)
from zope.interface import implements
from node.locking import locktree
from node.aliasing import (
    AliasedNodespace,
    DictAliaser,
)
from node.parts import (
    NodeChildValidate,
    Nodespaces,
    Adopt,
    Attributes,
    DefaultInit,
    Nodify,
    Storage,
    OdictStorage,
)
from node.ext.ugm import (
    User as BaseUserPart,
    Group as BaseGroupPart,
    Users as UsersPart,
    Groups as GroupsPart,
    Ugm as UgmPart,
)
from node.ext.ldap.interfaces import (
    ILDAPGroupsConfig as IGroupsConfig,
    ILDAPUsersConfig as IUsersConfig,
)
from node.ext.ldap.scope import ONELEVEL
from node.ext.ldap.debug import debug
from node.ext.ldap.bbb import LDAPNode


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


class PrincipalPart(Part):
    """Turns a node into a principal
    """
    
    @default
    def __init__(self, props, cfg):
        self.context = LDAPNode(name=cfg.baseDN, props=props)
        self.attraliaser = cfg.attrmap
        self.context._child_filter = cfg.queryFilter
        self.context._child_scope = int(cfg.scope)
        self.context._child_objectClasses = cfg.objectClasses
        self.context._key_attr = cfg.attrmap['id']
        self.context._rdn_attr = cfg.attrmap['rdn']
        self.context._seckey_attrs = ('dn',)
        if cfg.member_relation:
            self.context._child_relation = cfg.member_relation
    
    @default
    def ldap_attributes_factory(self, name=None, parent=None):
        if self.attraliaser is None:
            return self.context.attrs
        aliased_attrs = AliasedNodespace(self.context.attrs, self.attraliaser)
        aliased_attrs.allow_non_node_childs = True
        return aliased_attrs
    
    attributes_factory = finalize(ldap_attributes_factory)

    @default
    def idbydn(self, dn):
        """return a principals id for a given dn

        raise KeyError if not enlisted
        """
        self.context.keys()
        idsbydn = self.context._seckeys['dn']
        try:
            return idsbydn[dn]
        except KeyError:
            # It's possible that we got a different string resulting
            # in the same DN, as every components can have individual
            # comparison rules (see also
            # node.ext.ldap.bbb.LDAPNode.DN). We leave the job to ldap
            # and try again with the resulting DN.
            #
            # XXX: this was introduced because a customer has group
            # member attributes where the DN string differs.
            #
            # XXX: This would not be necessary, if an LDAP directory
            # is consistent, i.e does not use different strings to
            # talk about the same.
            #
            # XXX: normalization of DN in python would also be a
            # solution, but requires implementation of all comparison
            # rules defined in schemas. Maybe we can retrieve them
            # from LDAP.
            search = self.context.ldap_session.search
            try:
                dn = search(baseDN=dn)[0][0]
            except ldap.NO_SUCH_OBJECT:
                raise KeyError(dn)
            return idsbydn[dn]

    @extend
    def __repr__(self):
        return "<%s '%s'>" % (
                self.__class__.__name__.split('.')[-1],
                unicode(self.id).encode('ascii', 'replace'),
                )
    
    @default
    def add_role(self, role):
        """Add role.
        """
        raise NotImplementedError(u"``Principal`` does not implement "
                                  u"``add_role``")
    
    @default
    def remove_role(self, role):
        """Remove role.
        """
        raise NotImplementedError(u"``Principal`` does not implement "
                                  u"``remove_role``")
    
    @default
    @property
    def roles(self):
        """Roles.
        """
        raise NotImplementedError(u"``Principal`` does not implement "
                                  u"``roles``")


class UserPart(PrincipalPart, BaseUserPart):
    
    @default
    @property
    def groups(self):
        """List of groups this user is member of.
        """
        pass # XXX

    
class GroupPart(PrincipalPart, BaseGroupPart):
    
    @default
    @property
    def users(self):
        """List of users contained in this group.
        """
        pass #XXX
    
    @default
    @property
    def member_ids(self):
        """List of member ids contained in this group.
        """
        pass #XXX


class User(object):
    __metaclass__ = plumber
    __plumbing__ = (
        NodeChildValidate,
        Nodespaces,
        Attributes,
        Nodify,
        UserPart,
    )
    
    def __setitem__(self, key, value):
        raise NotImplementedError(u"User object cannot contain children.")


class Group(object):
    __metaclass__ = plumber
    __plumbing__ = (
        NodeChildValidate,
        Nodespaces,
        Attributes,
        Nodify,
        GroupPart,
    )
    
    @locktree
    def __setitem__(self, key, value):
        pass
    
    def __getitem__(self, key):
        return self.parent.parent.users[key]
    
    @locktree
    def __delitem__(self, key):
        pass
    
    def __iter__(self):
        for id in self.member_ids:
            yield id


class PrincipalsPart(Part):
    principals_factory = default(None)
    principal_attrmap = default(None)
    principal_attraliaser = default(None)
    
    @extend
    def __init__(self, props, cfg):
        self.context = LDAPNode(name=cfg.baseDN, props=props)
        self.context._seckey_attrs = ('dn',)
        
        self.context._child_filter = cfg.queryFilter
        self.context._child_scope = int(cfg.scope)
        self.context._child_objectClasses = cfg.objectClasses
        self.context._key_attr = cfg.attrmap['id']
        self.context._rdn_attr = cfg.attrmap['rdn']
        self.context._seckey_attrs = ('dn',)
        if cfg.member_relation:
            self.context._child_relation = cfg.member_relation
        
        self.principal_attrmap = cfg.attrmap
        self.principal_attraliaser = DictAliaser(cfg.attrmap)
        if cfg.attrmap['login'] != cfg.attrmap['id']:
            self.context._seckey_attrs += (cfg.attrmap['login'],)

    @default
    @property
    def __name__(self):
        return self.context.name

    # principals have ids
    @default
    @property
    def ids(self):
        return self.context.keys # XXX ??? keys()

    @default
    def __delitem__(self, key):
        del self.context[key]

    @default
    def __getitem__(self, key):
        # XXX: should use lazynodes caching, for now:
        # users['foo'] is not users['foo']
        principal = self.principal_factory(
                self.context[key],
                attraliaser=self.principal_attraliaser
                )
        principal.__name__ = self.context[key].name
        principal.__parent__ = self
        return principal

    @default
    def __iter__(self):
        return self.context.__iter__()

    @default
    def __setitem__(self, name, vessel):
        try:
            # XXX: better use attrs here. attrs does not necessarily need to be
            #      in a nodespace
            attrs = vessel.nodespaces['__attrs__']
        except KeyError:
            raise ValueError(u"Attributes need to be set.")

        if name in self:
            raise KeyError(u"Key already exists: '%s'." % (name,))

        nextvessel = AttributedNode()
        nextvessel.__name__ = name
        nextvessel.attribute_access_for_attrs = False
        principal = self.principal_factory(
                nextvessel,
                attraliaser=self.principal_attraliaser
                )
        principal.__name__ = name
        principal.__parent__ = self
        # XXX: cache
        for key, val in attrs.iteritems():
            principal.attrs[key] = val
        self.context[name] = nextvessel

    @default
    def _alias_dict(self, dct):
        if dct is None:
            return None
        # this code does not work if multiple keys map to same value
        #alias = self.principal_attraliaser.alias
        #aliased_dct = dict(
        #        [(alias(key), val) for key, val in dct.iteritems()]
        #        )
        #return aliased_dct
        # XXX: maybe some generalization in aliaser needed
        ret = dict()
        for key, val in self.principal_attraliaser.iteritems():
            for k, v in dct.iteritems():
                if val == k:
                    ret[key] = v
        return ret

    @default
    def _unalias_list(self, lst):
        if lst is None:
            return None
        unalias = self.principal_attraliaser.unalias
        return [unalias(x) for x in lst]

    @default
    def _unalias_dict(self, dct):
        if dct is None:
            return None
        unalias = self.principal_attraliaser.unalias
        unaliased_dct = dict(
                [(unalias(key), val) for key, val in dct.iteritems()]
                )
        return unaliased_dct

    @default
    def search(self, criteria=None, attrlist=None, exact_match=False,
               or_search=False):
        # XXX: stripped down for now, compare to LDAPNode.search
        # XXX: are single values always lists in results?
        #      is this what we want -> yes!
        results = self.context.search(
                criteria=self._unalias_dict(criteria),
                attrlist=self._unalias_list(attrlist),
                exact_match=exact_match,
                or_search=or_search,
                )
        if attrlist is None:
            return results
        aliased_results = \
                [(id, self._alias_dict(attrs)) for id, attrs in results]
        return aliased_results


class Users(object):
    __metaclass__ = plumber
    __plumbing__ = (
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        Nodify,
        PrincipalsPart,
        UsersPart,
    )
    
    principal_factory = User

    def __delitem__(self, id):
        user = self[id]
        for group_id in user.membership:
            del user.membership[group_id]
        super(Users, self).__delitem__(id)

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
    def authenticate(self, id=None, pw=None):
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


class Groups(object):
    __metaclass__ = plumber
    __plumbing__ = (
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        Nodify,
        PrincipalsPart,
        GroupsPart,
    )
    
    principal_factory = Group

    def __init__(self, props, cfg):
        if 'groupOfNames' in cfg.objectClasses:
            self._member_attr = 'member'
        elif 'groupOfUniqueNames' in cfg.objectClasses:
            self._member_attr = 'uniqueMember'
        elif 'posixGroup' in cfg.objectClasses:
            self._member_attr = 'memberUid'
        else:
            raise ValueError('Unsupported groups: %s' % (cfg.objectClasses,))
        cfg.attrmap[self._member_attr] = self._member_attr
        super(Groups, self).__init__(props, cfg)

    def __setitem__(self, key, vessel):
        vessel.attrs.setdefault(self._member_attr, []).insert(0, 'cn=nobody')
        super(Groups, self).__setitem__(key, vessel)


class Ugm(object):
    __metaclass__ = plumber
    __plumbing__ = (
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        DefaultInit,
        Nodify,
        UgmPart,
        OdictStorage,
    )
