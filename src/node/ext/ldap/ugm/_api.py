import ldap
from plumber import (
    plumber,
    plumb,
    default,
    extend,
    finalize,
    Part,
)
from zope.interface import implements
from node.base import AttributedNode
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
from node.utils import debug
from node.ext.ugm import (
    User as BaseUserPart,
    Group as BaseGroupPart,
    Users as BaseUsersPart,
    Groups as BaseGroupsPart,
    Ugm as BaseUgmPart,
)
from node.ext.ldap.interfaces import (
    ILDAPGroupsConfig as IGroupsConfig,
    ILDAPUsersConfig as IUsersConfig,
)
from node.ext.ldap.scope import ONELEVEL
from node.ext.ldap._node import LDAPNode


FORMAT_DN = 0
FORMAT_UID = 1


class PrincipalsConfig(object):
    """Superclass for UsersConfig, GroupsConfig and RolesConfig (later)
    """
    
    def __init__(self,
            baseDN='',
            attrmap={},
            scope=ONELEVEL,
            queryFilter='',
            objectClasses=[],
            member_relation='',
            defaults={},
            strict=True):
        self.baseDN = baseDN
        # XXX: never used. what was this supposed for?
        self.attrmap = attrmap
        self.scope = scope
        self.queryFilter = queryFilter
        self.objectClasses = objectClasses
        # XXX: never used. what was this supposed for?
        self.member_relation = member_relation
        self.defaults = defaults
        self.strict = strict


class UsersConfig(PrincipalsConfig):
    """Define how users look and where they are.
    """
    implements(IUsersConfig)


class GroupsConfig(PrincipalsConfig):
    """Define how groups look and where they are.
    """
    implements(IGroupsConfig)


class PrincipalAliasedAttributes(AliasedNodespace):
    
    allow_non_node_childs = True
    
    @property
    def changed(self):
        return self.context.changed

    def __call__(self):
        self.context()


class PrincipalPart(Part):
    
    @extend
    def __init__(self, context, attraliaser):
        self.context = context
        self.attraliaser = attraliaser
    
    @default
    def principal_attributes_factory(self, name=None, parent=None):
        if self.attraliaser is None:
            return self.context.attrs
        aliased_attrs = PrincipalAliasedAttributes(self.context.attrs,
                                                   self.attraliaser)
        return aliased_attrs
    
    attributes_factory = finalize(principal_attributes_factory)
    
    @default
    def add_role(self, role):
        self.parent.parent.add_role(role, self)
    
    @default
    def remove_role(self, role):
        self.parent.parent.remove_role(role, self)
    
    @default
    @property
    def roles(self):
        return self.parent.parent.roles(self)
    
    @default
    def __call__(self):
        self.context()


class UserPart(PrincipalPart, BaseUserPart):
    
    @default
    @property
    def groups(self):
        groups = self.parent.parent.groups
        format = groups._member_format
        attribute = groups._member_attribute
        if format == FORMAT_DN:
            criteria = { attribute: self.context.DN }
        elif format == FORMAT_UID:
            criteria = { attribute: self.context.attrs['uid'] }
        else:
            raise Exception(u"Unknow group format")
        res = groups.context.search(criteria=criteria)
        ret = list()
        for id in res:
            ret.append(groups[id])
        return ret


class User(object):
    __metaclass__ = plumber
    __plumbing__ = (
        UserPart,
        Nodespaces,
        Attributes,
        Nodify,
    )


class GroupPart(PrincipalPart, BaseGroupPart):
    
    @extend
    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return self.parent.parent.users[key]
    
    @extend
    @locktree
    def __delitem__(self, key):
        if key not in self:
            raise KeyError(key)
        if self._member_format == FORMAT_DN:
            val = self.parent.parent.users.context.child_dn(key)
        elif self._member_format == FORMAT_UID:
            val = key
        # self.context.attrs[self._member_attribute].remove won't work here
        # issue in LDAPNodeAttributes, does not recognize changed this way.
        members = self.context.attrs[self._member_attribute]
        members.remove(val)
        self.context.attrs[self._member_attribute] = members
        # XXX: call here immediately?
        self.context()
    
    @extend
    def __iter__(self):
        for id in self.member_ids:
            yield id
    
    @extend
    def __contains__(self, key):
        for id in self:
            if id == key:
                return True
        return False
    
    @default
    @locktree
    def add(self, key):
        if not key in self.member_ids:
            if self._member_format == FORMAT_DN:
                users = self.parent.parent.users
                # make sure user is loaded
                users[key]
                val = users.context.child_dn(key)
            elif self._member_format == FORMAT_UID:
                val = key
            # self.context.attrs[self._member_attribute].append won't work here
            # issue in LDAPNodeAttributes, does not recognize changed this way.
            old = self.context.attrs[self._member_attribute]
            self.context.attrs[self._member_attribute] = old + [val]
            # XXX: call here immediately?
            #self.context()
    
    @default
    @property
    def users(self):
        return [self.parent.parent.users[id] for id in self.member_ids]
    
    @default
    @property
    def member_ids(self):
        members = list()
        for member in self.context.attrs[self._member_attribute]:
            if member in ['nobody', 'cn=nobody']:
                continue
            members.append(member)
        if self._member_format == FORMAT_DN:
            return [self.parent.parent.users.idbydn(dn) for dn in members]
        if self._member_format == FORMAT_UID:
            return members
        raise Exception(u"Unknown member value format.")
    
    @default
    @property
    def _member_format(self):
        return self.parent._member_format
    
    @default
    @property
    def _member_attribute(self):
        return self.parent._member_attribute


class Group(object):
    __metaclass__ = plumber
    __plumbing__ = (
        GroupPart,
        NodeChildValidate,
        Nodespaces,
        Attributes,
        Nodify,
    )


class PrincipalsPart(Part):
    principal_attrmap = default(None)
    principal_attraliaser = default(None)
    
    @extend
    def __init__(self, props, cfg):
        self.context = LDAPNode(name=cfg.baseDN, props=props)
        self.context.search_filter = cfg.queryFilter
        self.context.search_scope = int(cfg.scope)
        
        # XXX: should this object classes be used for search and creation?
        self.context.child_defaults = dict()
        self.context.child_defaults['objectClass'] = cfg.objectClasses
        self.context.child_defaults.update(cfg.defaults)
        
        # XXX: make these attrs public
        self.context._key_attr = cfg.attrmap['id']
        self.context._rdn_attr = cfg.attrmap['rdn']
        
        if cfg.member_relation:
            self.context.search_relation = cfg.member_relation
        
        self.context._seckey_attrs = ('dn',)
        if cfg.attrmap.get('login') \
          and cfg.attrmap['login'] != cfg.attrmap['id']:
            self.context._seckey_attrs += (cfg.attrmap['login'],)
        
        self.principal_attrmap = cfg.attrmap
        self.principal_attraliaser = DictAliaser(cfg.attrmap, cfg.strict)
    
    @default
    def idbydn(self, dn):
        """Return a principal's id for a given dn.

        Raise KeyError if not enlisted.
        """
        self.context.keys()
        idsbydn = self.context._seckeys['dn']
        try:
            return idsbydn[dn]
        except KeyError:
            # It's possible that we got a different string resulting
            # in the same DN, as every components can have individual
            # comparison rules (see also node.ext.ldap._node.LDAPNode.DN).
            # We leave the job to LDAP and try again with the resulting DN.
            #
            # This was introduced because a customer has group
            # member attributes where the DN string differs.
            #
            # This would not be necessary, if an LDAP directory
            # is consistent, i.e does not use different strings to
            # talk about the same.
            #
            # Normalization of DN in python would also be a
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
    @property
    def ids(self):
        # XXX: do we really need this?
        return self.context.keys()

    @default
    def __delitem__(self, key):
        del self.context[key]

    @default
    def __getitem__(self, key):
        # XXX: should use lazynodes caching, for now:
        # users['foo'] is not users['foo']
        principal = self.principal_factory(
            self.context[key],
            attraliaser=self.principal_attraliaser)
        principal.__name__ = self.context[key].name
        principal.__parent__ = self
        return principal

    @default
    def __iter__(self):
        return self.context.__iter__()

    @default
    def __setitem__(self, name, vessel):
        try:
            attrs = vessel.attrs
        except AttributeError:
            raise ValueError(u"no attributes found, cannot convert.")
        if name in self:
            raise KeyError(u"Key already exists: '%s'." % (name,))
        nextvessel = AttributedNode()
        nextvessel.__name__ = name
        nextvessel.attribute_access_for_attrs = False
        principal = self.principal_factory(
            nextvessel,
            attraliaser=self.principal_attraliaser)
        principal.__name__ = name
        principal.__parent__ = self
        # XXX: cache
        for key, val in attrs.iteritems():
            principal.attrs[key] = val
        self.context[name] = nextvessel
    
    @default
    def __call__(self):
        self.context()

    @default
    def _alias_dict(self, dct):
        if dct is None:
            return None
        
        # this code does not work if multiple keys map to same value
        #alias = self.principal_attraliaser.alias
        #aliased_dct = dict(
        #    [(alias(key), val) for key, val in dct.iteritems()])
        #return aliased_dct
        
        # XXX: generalization in aliaser needed
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
            [(unalias(key), val) for key, val in dct.iteritems()])
        return unaliased_dct

    @default
    def search(self, criteria=None, attrlist=None,
               exact_match=False, or_search=False):
        results = self.context.search(
            criteria=self._unalias_dict(criteria),
            attrlist=self._unalias_list(attrlist),
            exact_match=exact_match,
            or_search=or_search)
        if attrlist is None:
            return results
        aliased_results = \
            [(id, self._alias_dict(attrs)) for id, attrs in results]
        return aliased_results
    
    @default
    def create(self, _id, **kw):
        vessel = AttributedNode()
        for k, v in kw.items():
            vessel.attrs[k] = v
        self[_id] = vessel
        return self[_id]


class UsersPart(PrincipalsPart, BaseUsersPart):
    
    principal_factory = default(User)

    @extend
    def __delitem__(self, id):
        user = self[id]
        try:
            groups = user.groups
        except AttributeError:
            groups = list()
        for group in groups:
            del group[user.name]
        del self.context[id]
    
    @default
    @debug
    def authenticate(self, id=None, pw=None):
        id = self.context._seckeys.get(
            self.principal_attrmap.get('login'), {}).get(id, id)
        try:
            userdn = self.context.child_dn(id)
        except KeyError:
            return False
        return self.context.ldap_session.authenticate(userdn, pw) \
            and id or False

    @default
    @debug
    def passwd(self, id, oldpw, newpw):
        self.context.ldap_session.passwd(
            self.context.child_dn(id), oldpw, newpw)


class Users(object):
    __metaclass__ = plumber
    __plumbing__ = (
        UsersPart,         
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        Nodify,
    )


def member_format(obj_cl):
    if 'groupOfNames' in obj_cl:
        return FORMAT_DN
    if 'groupOfUniqueNames' in obj_cl:
        return FORMAT_DN
    if 'posixGroup' in obj_cl:
        return FORMAT_UID
    raise Exception(u"Unknown format")


def member_attribute(obj_cl):
    if 'groupOfNames' in obj_cl:
        return 'member'
    if 'groupOfUniqueNames' in obj_cl:
        return 'uniqueMember'
    if 'posixGroup' in obj_cl:
        return 'memberUid'
    raise Exception(u"Unknown member attribute")


class GroupsPart(PrincipalsPart, BaseGroupsPart):
    
    principal_factory = default(Group)
    
    @default
    @property
    def _member_format(self):
        return member_format(self.context.child_defaults['objectClass'])
    
    @default
    @property
    def _member_attribute(self):
        return member_attribute(self.context.child_defaults['objectClass'])
    
    @plumb
    def __init__(_next, self, props, cfg):
        mem_attr = member_attribute(cfg.objectClasses)
        cfg.attrmap[mem_attr] = mem_attr
        _next(self, props, cfg)
    
    @plumb
    def __setitem__(_next, self, key, vessel):
        vessel.attrs.setdefault(
            self._member_attribute, []).insert(0, 'cn=nobody')
        _next(self, key, vessel)


class Groups(object):
    __metaclass__ = plumber
    __plumbing__ = (
        GroupsPart,         
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        Nodify,
    )


class UgmPart(BaseUgmPart):
    
    @extend
    def __init__(self, name=None, parent=None, props=None,
                 ucfg=None, gcfg=None, rcfg=None):
        """
        name
            node name
            
        parent
            node parent
            
        props
            LDAPProps
        
        ucfg
            UsersConfig
        
        gcfg
            GroupsConfig
        
        rcfg
            RolesConfig XXX: not yet
        """
        self.__name__ = name
        self.__parent__ = parent
        self.props = props
        self.ucfg = ucfg
        self.gcfg = gcfg
        self.rcfg = rcfg
    
    @extend
    def __getitem__(self, key):
        if not key in self.storage:
            if key == 'users':
                self['users'] = Users(self.props, self.ucfg)
            else:
                self['groups'] = Groups(self.props, self.gcfg)
        return self.storage[key]
    
    @extend
    @locktree
    def __setitem__(self, key, value):
        self._chk_key(key)
        self.storage[key] = value
    
    @extend
    def __delitem__(self, key):
        raise NotImplementedError(u"Operation forbidden on this node.")
    
    @extend
    def __iter__(self):
        for key in ['users', 'groups']:
            yield key
    
    @default
    @property
    def users(self):
        return self['users']
    
    @default
    @property
    def groups(self):
        return self['groups']
    
    @default
    def add_role(self, role, principal):
        # XXX
        raise NotImplementedError(u"not yet")
    
    @default
    def remove_role(self, role, principal):
        # XXX
        raise NotImplementedError(u"not yet")
        
    @default
    def roles(self, principal):
        # XXX
        raise NotImplementedError(u"not yet")
    
    @default
    def _chk_key(self, key):
        if not key in ['users', 'groups']:
            raise KeyError(key)


class Ugm(object):
    __metaclass__ = plumber
    __plumbing__ = (
        UgmPart,
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        DefaultInit,
        Nodify,
        OdictStorage,
    )