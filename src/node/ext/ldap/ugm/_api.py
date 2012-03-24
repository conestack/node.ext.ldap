# -*- coding: utf-8 -*-
import ldap
import types
import time
import logging
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
    OdictStorage,
)
from node.utils import debug
from node.ext.ugm import (
    User as UgmUser,
    Group as UgmGroup,
    Users as UgmUsers,
    Groups as UgmGroups,
    Ugm as UgmBase,
)
from node.ext.ldap.interfaces import (
    ILDAPGroupsConfig as IGroupsConfig,
    ILDAPUsersConfig as IUsersConfig,
)
from node.ext.ldap.scope import (
    BASE,
    ONELEVEL,
)
from node.ext.ldap.base import decode_utf8
from node.ext.ldap._node import LDAPNode
from node.ext.ldap.ugm.defaults import creation_defaults
from node.ext.ldap.ugm.samba import (
    sambaNTPassword,
    sambaLMPassword,
)


logger = logging.getLogger('node.ext.ldap')

# group member format
FORMAT_DN = 0
FORMAT_UID = 1

# expiration unit
EXPIRATION_DAYS = 0
EXPIRATION_SECONDS = 1


class AccountExpired(object):
    
    def __nonzero__(self):
        return False
    
    def __repr__(self):
        return 'ACCOUNT_EXPIRED'
    
    __str__ = __repr__
    
ACCOUNT_EXPIRED = AccountExpired()


class PrincipalsConfig(object):
    
    def __init__(self, baseDN='', attrmap={}, scope=ONELEVEL, queryFilter='',
                 objectClasses=[], defaults={}, strict=True,
                 memberOfSupport=False, expiresAttr=None,
                 expiresUnit=EXPIRATION_DAYS):
        self.baseDN = baseDN
        self.attrmap = attrmap
        self.scope = scope
        self.queryFilter = queryFilter
        self.objectClasses = objectClasses
        self.defaults = defaults
        self.strict = strict
        self.memberOfSupport = memberOfSupport
        # XXX: currently expiresAttr only gets considered for user
        #      authentication group and role expiration is not implemented yet.
        self.expiresAttr = expiresAttr
        self.expiresUnit = expiresUnit
        # XXX: member_relation
        #self.member_relation = member_relation


class UsersConfig(PrincipalsConfig):
    """Define how users look and where they are.
    """
    implements(IUsersConfig)


class GroupsConfig(PrincipalsConfig):
    """Define how groups look and where they are.
    """
    implements(IGroupsConfig)


class RolesConfig(PrincipalsConfig):
    """Define how roles are mapping in LDAP. Basically a role mapping works
    like a group mapping, but the id attribute is considered as the role name,
    and the members set have this role granted.
    """


class PrincipalAliasedAttributes(AliasedNodespace):
    
    allow_non_node_childs = True
    
    @property
    def changed(self):
        return self.context.changed


class AliasedPrincipal(Part):
    
    @extend
    def __init__(self, context, attraliaser):
        self.context = context
        self.attraliaser = attraliaser
    
    @default
    def principal_attributes_factory(self, name=None, parent=None):
        aliased_attrs = PrincipalAliasedAttributes(self.context.attrs,
                                                   self.attraliaser)
        return aliased_attrs
    
    attributes_factory = finalize(principal_attributes_factory)
    
    @default
    @locktree
    def __call__(self):
        self.context()


class LDAPPrincipal(AliasedPrincipal):
    
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
    @property
    def changed(self):
        return self.context.changed
    
    @default
    @property
    def member_of_attr(self):
        """memberOf is in openldap realized as overlay and in Active
        Directory also computed. In case of openldap this attribute is not
        delivered in LDAP response unless explicitly queried. Thus a separate
        property is used to query memberOf information explicit.
        """
        entry = self.context.ldap_session.search(
            scope=BASE,
            baseDN=self.context.DN,
            force_reload=self.context._reload,
            attrlist=['memberOf'])
        return entry[0][1].get('memberOf', list())


class LDAPUser(LDAPPrincipal, UgmUser):
    
    @default
    @property
    def groups(self):
        groups = self.parent.parent.groups
        if self.parent.parent.ucfg.memberOfSupport:
            res = list()
            for dn in self.member_of_attr:
                try:
                    res.append(groups.idbydn(dn))
                except KeyError:
                    # happens if DN is returned which does not fit the groups
                    # base DN.
                    pass
        else:
            member_format = groups._member_format
            attribute = groups._member_attribute
            if member_format == FORMAT_DN:
                criteria = { attribute: self.context.DN }
            elif member_format == FORMAT_UID:
                criteria = { attribute: self.context.attrs['uid'] }
            # if roles configuration points to child of groups container, and
            # group configuration has search scope SUBTREE, and groups are
            # specified by the same criteria as roles, the search returns the 
            # role id's as well.
            # XXX: such edge cases should be resolved at UGM init time
            res = groups.context.search(criteria=criteria)
        ret = list()
        for uid in res:
            ret.append(groups[uid])
        return ret


class User(object):
    __metaclass__ = plumber
    __plumbing__ = (
        LDAPUser,
        Nodespaces,
        Attributes,
        Nodify,
    )


class LDAPGroupMapping(Part):
    
    @extend
    def __getitem__(self, key):
        key = decode_utf8(key)
        if key not in self:
            raise KeyError(key)
        return self.related_principals(key)[key]
    
    @extend
    @locktree
    def __delitem__(self, key):
        key = decode_utf8(key)
        if key not in self:
            raise KeyError(key)
        if self._member_format == FORMAT_DN:
            val = self.related_principals(key).context.child_dn(key)
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
        return iter(self.member_ids)
    
    @extend
    def __contains__(self, key):
        key = decode_utf8(key)
        for uid in self:
            if uid == key:
                return True
        return False
    
    @default
    @locktree
    def add(self, key):
        key = decode_utf8(key)
        if not key in self.member_ids:
            val = self.translate_key(key)
            # self.context.attrs[self._member_attribute].append won't work here
            # issue in LDAPNodeAttributes, does not recognize changed this way.
            old = self.context.attrs.get(self._member_attribute, list())
            self.context.attrs[self._member_attribute] = old + [val]
            # XXX: call here immediately?
            #self.context()
    
    @default
    @property
    def member_ids(self):
        ugm = self.parent.parent
        if ugm:
            # XXX: roles with memberOf use rcfg!
            gcfg = ugm.gcfg
            if gcfg and gcfg.memberOfSupport:
                users = ugm.users
                criteria = {
                    'memberOf': self.context.DN,
                }
                # XXX: use users instead of users.context.
                #      Problem: Aliaed Attributes in strict mode do not know
                #               about memberOf by default. Check for related
                #               configuration flag and set transparently 
                return users.context.search(criteria=criteria)
        ret = list()
        members = self.context.attrs.get(self._member_attribute, list())
        for member in members:
            if member in ['nobody', 'cn=nobody']:
                continue
            ret.append(member)
        ret = self.translate_ids(ret)
        keys = self.existing_member_ids
        ret = [uid for uid in ret if uid in keys]
        return ret
    
    @default
    @property
    def _member_format(self):
        return self.parent._member_format
    
    @default
    @property
    def _member_attribute(self):
        return self.parent._member_attribute


class LDAPGroup(LDAPGroupMapping, LDAPPrincipal, UgmGroup):
    
    @default
    def related_principals(self, key=None):
        return self.parent.parent.users
    
    @default
    @property
    def users(self):
        return [self.parent.parent.users[uid] for uid in self.member_ids]
    
    @default
    @property
    def existing_member_ids(self):
        return self.related_principals().keys()
    
    @default
    def translate_ids(self, members):
        if self._member_format != FORMAT_DN:
            return members
        principals = self.related_principals()
        translated = list()
        for dn in members:
            try:
                translated.append(principals.idbydn(dn))
            except KeyError:
                # inexistent DN
                pass
        return translated
    
    @default
    def translate_key(self, key):
        ret = None
        if self._member_format == FORMAT_DN:
            principals = self.related_principals()
            # make sure principal is loaded
            principals[key]
            ret = principals.context.child_dn(key)
        elif self._member_format == FORMAT_UID:
            ret = key
        return ret


class Group(object):
    __metaclass__ = plumber
    __plumbing__ = (
        LDAPGroup,
        NodeChildValidate,
        Nodespaces,
        Attributes,
        Nodify,
    )


class LDAPPrincipals(OdictStorage):
    principal_attrmap = default(None)
    principal_attraliaser = default(None)
    
    @extend
    def __init__(self, props, cfg):
        context = LDAPNode(name=cfg.baseDN, props=props)
        context.search_filter = cfg.queryFilter
        context.search_scope = int(cfg.scope)
        
        context.child_defaults = dict()
        context.child_defaults['objectClass'] = cfg.objectClasses
        if hasattr(cfg, 'defaults'):
            context.child_defaults.update(cfg.defaults)
        for oc in cfg.objectClasses:
            for key, val in creation_defaults.get(oc, dict()).items():
                if not key in context.child_defaults:
                    context.child_defaults[key] = val
        
        # XXX: make these attrs public
        context._key_attr = cfg.attrmap['id']
        context._rdn_attr = cfg.attrmap['rdn']
        
        #if cfg.member_relation:
        #    context.search_relation = cfg.member_relation
        
        context._seckey_attrs = ('dn',)
        if cfg.attrmap.get('login') \
          and cfg.attrmap['login'] != cfg.attrmap['id']:
            context._seckey_attrs += (cfg.attrmap['login'],)
        
        context._load_keys()
        
        self.expiresAttr = getattr(cfg, 'expiresAttr', None)
        self.expiresUnit = getattr(cfg, 'expiresUnit', None)
        self.principal_attrmap = cfg.attrmap
        self.principal_attraliaser = DictAliaser(cfg.attrmap, cfg.strict)
        self.context = context
    
    @default
    def idbydn(self, dn, strict=False):
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
            if strict:
                raise KeyError(dn)
            search = self.context.ldap_session.search
            try:
                dn = search(baseDN=dn)[0][0]
            except ldap.NO_SUCH_OBJECT:
                raise KeyError(dn)
            return idsbydn[dn]

    @extend
    @property
    def ids(self):
        return self.context.keys()

    @default
    @locktree
    def __delitem__(self, key):
        key = decode_utf8(key)
        del self.context[key]
        try:
            del self.storage[key]
        except KeyError:
            pass

    @default
    @locktree
    def __getitem__(self, key):
        key = decode_utf8(key)
        try:
            return self.storage[key]
        except KeyError:
            principal = self.principal_factory(
                self.context[key],
                attraliaser=self.principal_attraliaser)
            principal.__name__ = self.context[key].name
            principal.__parent__ = self
            self.storage[key] = principal
            return principal

    @default
    @locktree
    def __iter__(self):
        return self.context.__iter__()

    @default
    @locktree
    def __setitem__(self, name, vessel):
        """XXX: mechanism for defining a target container if search scope is
                SUBTREE
        """
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
    @property
    def changed(self):
        return self.context.changed
    
    @default
    @locktree
    def invalidate(self, key=None):
        """Invalidate LDAPPrincipals.
        """
        key = decode_utf8(key)
        self.context.invalidate(key)
        if key is None:
            self.storage.clear()
            return
        try:
            del self.storage[key]
        except KeyError:
            pass
    
    @default
    @locktree
    def __call__(self):
        self.context()

    @default
    def _alias_dict(self, dct):
        # XXX: seem to be not reached at all
        #if dct is None:
        #    return None
        
        # XXX: this code does not work if multiple keys map to same value
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
               exact_match=False, or_search=False, or_keys=None, or_values=None,
               page_size=None, cookie=None):
        results = self.context.search(
            criteria=self._unalias_dict(criteria),
            attrlist=self._unalias_list(attrlist),
            exact_match=exact_match,
            or_search=or_search,
            or_keys=or_keys,
            or_values=or_values,
            page_size=page_size,
            cookie=cookie
            )
        if type(results) is tuple:
            results, cookie = results
        if attrlist is not None:
            results = [(uid, self._alias_dict(attrs)) for uid, attrs in results]
        if cookie is not None:
            return results, cookie
        return results
 
    @default
    @locktree
    def create(self, pid, **kw):
        vessel = AttributedNode()
        for k, v in kw.items():
            vessel.attrs[k] = v
        self[pid] = vessel
        return self[pid]


class LDAPUsers(LDAPPrincipals, UgmUsers):
    
    principal_factory = default(User)

    @extend
    @locktree
    def __delitem__(self, key):
        key = decode_utf8(key)
        user = self[key]
        try:
            groups = user.groups
        except AttributeError:
            groups = list()
        for group in groups:
            del group[user.name]
        parent = self.parent
        if parent and parent.rcfg is not None:
            for role in user.roles:
                user.remove_role(role)
        del self.context[key]
    
    @default
    def id_for_login(self, login):
        return self.context._seckeys.get(
            self.principal_attrmap.get('login'), {}).get(login, login)
    
    @default
    @debug
    def authenticate(self, id=None, pw=None):
        # XXX: rename 'id' kw arg to 'login'
        id = decode_utf8(id)
        id = self.id_for_login(id)
        try:
            if self.expiresAttr:
                user = self.context[id]
                expires = user.attrs.get(self.expiresAttr)
                if expires and expires not in ['99999' '-1']:
                    # check expiration timestamp
                    try:
                        expires = int(expires)
                    except ValueError:
                        # unknown expires field data
                        msg= u"Accound expiration flag for user '%s' " +\
                             u"contains unknown data"
                        msg = msg % id
                        logger.error(msg)
                        return False
                    
                    # XXX: maybe configurable?
                    # shadow account specific
                    #if self.expiresAttr == 'shadowExpire':
                    #    expires += int(user.attrs.get('shadowInactive', '0'))
                    # /XXX
                    
                    days = time.time()
                    if self.expiresUnit == EXPIRATION_DAYS:
                        # numer of days since epoch
                        days /= 86400
                    if days >= expires:
                        return ACCOUNT_EXPIRED
                userdn = user.DN
            else:
                userdn = self.context.child_dn(id)
        except KeyError:
            return False
        return self.context.ldap_session.authenticate(userdn, pw) \
            and id or False

    @default
    @debug
    def passwd(self, id, oldpw, newpw):
        id = decode_utf8(id)
        self.context.ldap_session.passwd(
            self.context.child_dn(id), oldpw, newpw)
        object_classes = self.context.child_defaults['objectClass']
        user_node = self[id].context
        user_node.attrs.load()
        if 'sambaSamAccount' in object_classes:
            user_node.attrs['sambaNTPassword'] = sambaNTPassword(newpw)
            user_node.attrs['sambaLMPassword'] = sambaLMPassword(newpw)
            user_node()


class Users(object):
    __metaclass__ = plumber
    __plumbing__ = (
        LDAPUsers,         
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
    if 'group' in obj_cl:
        return FORMAT_DN
    raise Exception(u"Unknown format")


def member_attribute(obj_cl):
    if 'groupOfNames' in obj_cl:
        return 'member'
    if 'groupOfUniqueNames' in obj_cl:
        return 'uniqueMember'
    if 'posixGroup' in obj_cl:
        return 'memberUid'
    if 'group' in obj_cl:
        return 'member' # XXX: check AD!
    raise Exception(u"Unknown member attribute")


class LDAPGroupsMapping(LDAPPrincipals, UgmGroups):
    
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
        # XXX: kick this, dummy member should be created by default value
        #      callback
        if self._member_format is FORMAT_UID:
            vessel.attrs.setdefault(
                self._member_attribute, []).insert(0, 'nobody')
        else:
            vessel.attrs.setdefault(
                self._member_attribute, []).insert(0, 'cn=nobody')
        _next(self, key, vessel)


class LDAPGroups(LDAPGroupsMapping):
    
    principal_factory = default(Group)
    
    @extend
    @locktree
    def __delitem__(self, key):
        key = decode_utf8(key)
        group = self[key]
        parent = self.parent
        if parent and parent.rcfg is not None:
            for role in group.roles:
                group.remove_role(role)
        del self.context[key]


class Groups(object):
    __metaclass__ = plumber
    __plumbing__ = (
        LDAPGroups,         
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        Nodify,
    )


class LDAPRole(LDAPGroupMapping, AliasedPrincipal):
    
    @default
    def related_principals(self, key):
        ugm = self.parent.parent
        if key.startswith('group:'):
            return ugm.groups
        return ugm.users
    
    @default
    @property
    def existing_member_ids(self):
        ugm = self.parent.parent
        users = ugm.users
        groups = ugm.groups
        ret = [key for key in users]
        for key in groups:
            ret.append('group:%s' % key)
        return ret
    
    @default
    def translate_ids(self, members):
        if self._member_format == FORMAT_DN:
            ugm = self.parent.parent
            users = ugm.users
            groups = ugm.groups
            user_members = list()
            for dn in members:
                try:
                    user_members.append(users.idbydn(dn, True))
                except KeyError:
                    pass
            group_members = list()
            for dn in members:
                try:
                    group_members.append('group:%s' % groups.idbydn(dn, True))
                except KeyError:
                    pass
            members = user_members + group_members
        return members
    
    @default
    def translate_key(self, key):
        ret = None
        if self._member_format == FORMAT_DN:
            if key.startswith('group:'):
                key = key[6:]
                principals = self.parent.parent.groups
            else:
                principals = self.parent.parent.users
            # make sure principal is loaded
            principals[key]
            ret = principals.context.child_dn(key)
        elif self._member_format == FORMAT_UID:
            ret = key
        return ret
    
    @extend
    @locktree
    def __getitem__(self, key):
        key = decode_utf8(key)
        if key not in self:
            raise KeyError(key)
        principals = self.related_principals(key)
        if key.startswith('group:'):
            key = key[6:]
        return principals[key]
    
    @extend
    @locktree
    def __delitem__(self, key):
        key = decode_utf8(key)
        if key not in self:
            raise KeyError(key)
        principals = self.related_principals(key)
        if self._member_format == FORMAT_DN:
            real_key = key
            if key.startswith('group:'):
                real_key = key[6:]
            val = principals.context.child_dn(real_key)
        elif self._member_format == FORMAT_UID:
            val = key
        # self.context.attrs[self._member_attribute].remove won't work here
        # issue in LDAPNodeAttributes, does not recognize changed this way.
        members = self.context.attrs[self._member_attribute]
        members.remove(val)
        self.context.attrs[self._member_attribute] = members
        # XXX: call here immediately?
        self.context()


class Role(object):
    __metaclass__ = plumber
    __plumbing__ = (
        LDAPRole,
        NodeChildValidate,
        Nodespaces,
        Attributes,
        Nodify,
    )


class LDAPRoles(LDAPGroupsMapping):
    
    principal_factory = default(Role)


class Roles(object):
    __metaclass__ = plumber
    __plumbing__ = (
        LDAPRoles,         
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        Nodify,
    )


class LDAPUgm(UgmBase):
    
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
            RolesConfig
        """
        self.__name__ = name
        self.__parent__ = parent
        self.props = props
        self.ucfg = ucfg
        self.gcfg = gcfg
        self.rcfg = rcfg
    
    @extend
    @locktree
    def __getitem__(self, key):
        if not key in self.storage:
            if key == 'users':
                self['users'] = Users(self.props, self.ucfg)
            elif key == 'groups':
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
    
    @extend
    @locktree
    def __call__(self):
        self.users()
        self.groups()
        roles_storage = self.roles_storage
        if roles_storage is not None:
            roles_storage()
    
    @default
    @property
    def users(self):
        return self['users']
    
    @default
    @property
    def groups(self):
        return self['groups']
    
    @default
    @property
    def roles_storage(self):
        return self._roles
    
    @default
    @locktree
    def roles(self, principal):
        uid = self._principal_id(principal)
        roles = self._roles
        ret = list()
        if roles is None:
            # XXX: logging
            return ret        
        for role in roles.values():
            if uid in role.member_ids:
                ret.append(role.name)
        return ret

# XXX: Below is the logic for querying roles from LDAP via query. Integrate
#      to use this logic whenever roles are queried and the roles node is
#      unchanged.
#        attribute = roles._member_attribute
#        format = roles._member_format
#        if format == FORMAT_DN:
#            criteria = { attribute: principal.context.DN }
#        elif format == FORMAT_UID:
#            # XXX: this is hacky. we really need member relations!!!
#            if isinstance(principal, Group):
#                attrkey = principal.parent.context._rdn_attr
#                value = 'group:%s' % principal.context.attrs[attrkey]
#            else:
#                value = principal.context.attrs['uid']
#            criteria = { attribute: value }
#        return roles.context.search(criteria=criteria)
    
    @default
    @locktree
    def add_role(self, rolename, principal):
        uid = self._principal_id(principal)
        roles = self._roles
        if roles is None:
            raise ValueError(u"Role support not configured properly")
        role = roles.get(rolename)
        if role is None:
            role = roles.create(rolename)
        if uid in role.member_ids:
            raise ValueError(u"Principal already has role '%s'" % rolename)
        role.add(uid)
    
    @default
    @locktree
    def remove_role(self, rolename, principal):
        uid = self._principal_id(principal)
        roles = self._roles
        if roles is None:
            raise ValueError(u"Role support not configured properly")
        role = roles.get(rolename)
        if role is None:
            raise ValueError(u"Role not exists '%s'" % rolename)
        if not uid in role.member_ids:
            raise ValueError(u"Principal does not has role '%s'" % rolename)
        del role[uid]
        if not role.member_ids:
            parent = role.parent
            del parent[rolename]
    
    @default
    @property
    def _roles(self):
        if not 'roles' in self.storage:
            try:
                roles = Roles(self.props, self.rcfg)
            except Exception:
                # XXX: logging
                return None
            roles.__name__ = 'roles'
            roles.__parent__ = self
            self.storage['roles'] = roles
        return self.storage['roles']
    
    @default
    def _principal_id(self, principal):
        uid = principal.name
        if isinstance(principal, Group):
            uid = 'group:%s' % uid
        return uid
    
    @default
    def _chk_key(self, key):
        if not key in ['users', 'groups']:
            raise KeyError(key)


class Ugm(object):
    __metaclass__ = plumber
    __plumbing__ = (
        LDAPUgm,
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        DefaultInit,
        Nodify,
        OdictStorage,
    )
