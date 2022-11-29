# -*- coding: utf-8 -*-
from datetime import datetime
from ldap.dn import explode_dn
from node.behaviors import Alias
from node.behaviors import Attributes
from node.behaviors import DefaultInit
from node.behaviors import MappingAdopt
from node.behaviors import MappingConstraints
from node.behaviors import MappingNode
from node.behaviors import MappingStorage
from node.behaviors import OdictStorage
from node.behaviors.alias import DictAliaser
from node.ext.ldap._node import LDAPNode
from node.ext.ldap.base import ensure_text
from node.ext.ldap.interfaces import ILDAPGroupsConfig as IGroupsConfig
from node.ext.ldap.interfaces import ILDAPUsersConfig as IUsersConfig
from node.ext.ldap.scope import BASE
from node.ext.ldap.scope import ONELEVEL
from node.ext.ldap.ugm.defaults import creation_defaults
from node.ext.ldap.ugm.expires import AccountExpiration
from node.ext.ldap.ugm.expires import EXPIRATION_DAYS
from node.ext.ldap.ugm.expires import EXPIRATION_SECONDS  # noqa
from node.ext.ldap.ugm.expires import account_expiration
from node.ext.ldap.ugm.samba import sambaLMPassword
from node.ext.ldap.ugm.samba import sambaNTPassword
from node.ext.ugm import Group as UgmGroup
from node.ext.ugm import Groups as UgmGroups
from node.ext.ugm import Ugm as UgmBase
from node.ext.ugm import User as UgmUser
from node.ext.ugm import Users as UgmUsers
from node.locking import locktree
from node.utils import debug
from plumber import Behavior
from plumber import default
from plumber import finalize
from plumber import override
from plumber import plumb
from plumber import plumbing
from zope.interface import implementer
import ldap
import logging
import six
import time


logger = logging.getLogger('node.ext.ldap')

# group member format
FORMAT_DN = 0
FORMAT_UID = 1

# mapping from object-class to properties
MEMBER_LOOKUP_BY_CLASS = {
    'groupOfNames': {
        'format': FORMAT_DN,
        'attribute': 'member',
    },
    'groupOfUniqueNames': {
        'format': FORMAT_DN,
        'attribute': 'uniqueMember',
    },
    'posixGroup': {
        'format': FORMAT_UID,
        'attribute': 'memberUid',
    },
    'group': {
        'format': FORMAT_DN,
        'attribute': 'member',
    },
}


class PrincipalsConfig(object):

    def __init__(
        self,
        baseDN='',
        attrmap={},
        scope=ONELEVEL,
        queryFilter='',
        objectClasses=[],
        defaults={},
        strict=True,
        memberOfSupport=False,
        recursiveGroups=False,
        memberOfExternalGroupDNs=[],
        expiresAttr=None,
        expiresUnit=EXPIRATION_DAYS
    ):
        self.baseDN = baseDN
        self.attrmap = attrmap
        self.scope = scope
        self.queryFilter = queryFilter
        self.objectClasses = objectClasses
        self.defaults = defaults
        self.strict = strict
        self.memberOfSupport = memberOfSupport
        self.recursiveGroups = recursiveGroups
        self.memberOfExternalGroupDNs = memberOfExternalGroupDNs
        # XXX: member_relation
        # self.member_relation = member_relation

        # Expiration related settings only get considered for users
        # XXX: move to ``ILDAPUsersConfig``
        self.expiresAttr = expiresAttr
        self.expiresUnit = expiresUnit


@implementer(IUsersConfig)
class UsersConfig(PrincipalsConfig):
    """Define how users look and where they are.
    """


@implementer(IGroupsConfig)
class GroupsConfig(PrincipalsConfig):
    """Define how groups look and where they are.
    """


class RolesConfig(PrincipalsConfig):
    """Define how roles are mapping in LDAP. Basically a role mapping works
    like a group mapping, but the id attribute is considered as the role name,
    and the members set have this role granted.
    """


@plumbing(
    Alias,
    MappingConstraints,
    MappingAdopt,
    MappingNode,
    MappingStorage)
class PrincipalAliasedAttributes(object):
    child_constraints = None

    def __init__(self, context, aliaser=None):
        """
        :param context: The node whose children to alias
        :param aliaser: The aliaser to be used
        """
        self.__name__ = context.name
        self.__parent__ = None
        self.context = context
        self.aliaser = aliaser

    @property
    def storage(self):
        return self.context

    @property
    def changed(self):
        return self.context.changed

    def __repr__(self):
        return "Aliased " + self.context.__repr__()


class AliasedPrincipal(Behavior):

    @override
    def __init__(self, context, attraliaser):
        self.context = context
        self.attraliaser = attraliaser

    @default
    def principal_attributes_factory(self, name=None, parent=None):
        aliased_attrs = PrincipalAliasedAttributes(
            self.context.attrs,
            self.attraliaser
        )
        return aliased_attrs

    attributes_factory = finalize(principal_attributes_factory)

    @default
    @locktree
    def __call__(self):
        # add object classes from creation defaults. if missing.
        # happens if object classes are added after principals were already
        # created with another set of default object classes or if editing
        # existing principals from a database not created with this
        # API/configuration.
        ocs = self.context.attrs['objectClass']
        ocs = [ocs] if isinstance(ocs, six.text_type) else ocs
        ocsc = len(ocs)
        for oc in self.parent.context.child_defaults['objectClass']:
            if oc not in ocs:
                ocs.append(oc)
        # reset object classes only if changed to avoid unnecessary write
        # operations to LDAP backend
        if ocsc != len(ocs):
            self.context.attrs['objectClass'] = ocs
        # finally persist
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
            attrlist=['memberOf']
        )
        return entry[0][1].get('memberOf', list())


class LDAPUser(LDAPPrincipal, UgmUser):

    @default
    @property
    def groups(self):
        groups = self.parent.parent.groups
        return [groups[uid] for uid in self.group_ids if uid in groups]

    @default
    @property
    def group_ids(self):
        groups = self.parent.parent.groups
        if self.parent.parent.ucfg.memberOfSupport:
            group_dns = [groups.context.DN]
            group_dns += self.parent.parent.ucfg.memberOfExternalGroupDNs
            res = list()
            for dn in self.member_of_attr:
                dn = ensure_text(dn)
                matching_group_dns = {
                    gdn for gdn in group_dns
                    if dn.endswith(gdn)
                }
                if not matching_group_dns:
                    # Skip DN outside groups base DN
                    continue
                try:
                    res.append(groups.idbydn(dn))
                except KeyError:
                    # happens if DN is returned which does not fit the groups
                    # base DN.
                    pass
        else:
            member_format = groups._member_format
            attribute = groups._member_attribute
            # Support LDAP_MATCHING_RULE_IN_CHAIN (recursive/nested groups)
            # See https://msdn.microsoft.com/en-us/library/aa746475(v=vs.85).aspx
            if self.parent.parent.ucfg.recursiveGroups:
                attribute += ':1.2.840.113556.1.4.1941:'
            if member_format == FORMAT_DN:
                criteria = {attribute: self.context.DN}
            elif member_format == FORMAT_UID:
                criteria = {attribute: self.context.attrs['uid']}
            attrlist = [groups._key_attr]
            # if roles configuration points to child of groups container, and
            # group configuration has search scope SUBTREE, and groups are
            # specified by the same criteria as roles, the search returns the
            # role id's as well.
            # XXX: such edge cases should be resolved at UGM init time
            matches_generator = groups.context.batched_search(
                criteria=criteria,
                attrlist=attrlist
            )
            res = [att[groups._key_attr][0] for _, att in matches_generator]
        return res

    @default
    @property
    def expired(self):
        account_expires = self.parent.account_expires
        if not account_expires:
            return False
        return account_expires.expired(self.context.attrs)

    @property
    def expires(self):
        account_expires = self.parent.account_expires
        if not account_expires:
            return None
        return account_expires.get(self.context.attrs)

    @override
    @expires.setter
    def expires(self, value):
        account_expires = self.parent.account_expires
        if not account_expires:
            return
        account_expires.set(self.context.attrs, value)


@plumbing(
    LDAPUser,
    Attributes,
    MappingNode)
class User(object):
    pass


class LDAPGroupMapping(Behavior):

    @override
    def __getitem__(self, key):
        key = ensure_text(key)
        if key not in self:
            raise KeyError(key)
        return self.related_principals(key)[key]

    @override
    @locktree
    def __delitem__(self, key):
        key = ensure_text(key)
        if key not in self:
            raise KeyError(key)
        if self._member_format == FORMAT_DN:
            val = self.related_principals(key)[key].context.DN
        elif self._member_format == FORMAT_UID:
            val = key
        # self.context.attrs[self._member_attribute].remove won't work here
        # issue in LDAPNodeAttributes, does not recognize changed this way.
        members = self.context.attrs[self._member_attribute]
        members.remove(val)
        self.context.attrs[self._member_attribute] = members
        # XXX: call here immediately?
        self.context()

    @override
    def __iter__(self):
        return iter(self.member_ids)

    @override
    def __contains__(self, key):
        key = ensure_text(key)
        for uid in self:
            if uid == key:
                return True
        return False

    @default
    @locktree
    def add(self, key):
        key = ensure_text(key)
        if key not in self.member_ids:
            val = self.translate_key(key)
            # self.context.attrs[self._member_attribute].append won't work here
            # issue in LDAPNodeAttributes, does not recognize changed this way.
            old = self.context.attrs.get(self._member_attribute, list())
            self.context.attrs[self._member_attribute] = old + [val]
            # XXX: call here immediately?
            # self.context()

    @default
    @property
    def member_ids(self):
        ugm = self.parent.parent
        if ugm:
            # XXX: roles with memberOf use rcfg!
            gcfg = ugm.gcfg
            if gcfg and gcfg.memberOfSupport:
                users = ugm.users
                criteria = {'memberOf': self.context.DN}
                attrlist = [users._key_attr]
                matches_generator = users.context.batched_search(
                    criteria=criteria,
                    attrlist=attrlist
                )
                return [
                    att[users._key_attr][0] for _, att in matches_generator
                ]
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
            principal = principals[key]
            ret = principal.context.DN
        elif self._member_format == FORMAT_UID:
            ret = key
        return ret


@plumbing(
    LDAPGroup,
    MappingConstraints,
    Attributes,
    MappingNode)
class Group(object):
    pass


class LDAPPrincipals(OdictStorage):
    principal_attrmap = default(None)
    principal_attraliaser = default(None)

    @override
    def __init__(self, props, cfg):
        context = LDAPNode(name=cfg.baseDN, props=props)
        context.search_filter = cfg.queryFilter
        context.search_scope = int(cfg.scope)
        context.child_defaults = dict()
        context.child_defaults['objectClass'] = cfg.objectClasses
        context.child_defaults.update(cfg.defaults)
        for oc in cfg.objectClasses:
            for key, val in creation_defaults.get(oc, dict()).items():
                if key not in context.child_defaults:
                    context.child_defaults[key] = val
        # if cfg.member_relation:
        #     context.search_relation = cfg.member_relation
        self._rdn_attr = cfg.attrmap['rdn']
        self._key_attr = cfg.attrmap['id']
        if self._key_attr not in cfg.attrmap:
            cfg.attrmap[self._key_attr] = self._key_attr
        self._login_attr = cfg.attrmap['id']
        if cfg.attrmap.get('login'):
            self._login_attr = cfg.attrmap['login']
        self.principal_attrmap = cfg.attrmap
        self.principal_attraliaser = DictAliaser(cfg.attrmap, cfg.strict)
        self.context = context
        # Expiration related settings only get considered for users
        # XXX: move to ``LDAPUsers``
        expiresAttr = getattr(cfg, 'expiresAttr', None)
        expiresUnit = getattr(cfg, 'expiresUnit', None)
        self.account_expires = None
        if not expiresAttr:
            return
        account_expires = account_expiration.get(expiresAttr)
        if not account_expires:
            account_expires = AccountExpiration(
                attribute=expiresAttr,
                unit=expiresUnit
            )
        self.account_expires = account_expires

    @default
    def idbydn(self, dn, strict=False):
        """Return a principal's id for a given dn.

        Raise KeyError if not enlisted.
        """
        # XXX: rename to id_by_dn
        # XXX: what was strict good for? remove
        # if strict:
        #     raise KeyError(dn)
        try:
            search = self.context.ldap_session.search
            res = search(baseDN=dn)[0]
            return ensure_text(res[1][self._key_attr][0])
        except ldap.NO_SUCH_OBJECT:
            raise KeyError(dn)

    @override
    @property
    def ids(self):
        return list(self.__iter__())

    @default
    @locktree
    def __delitem__(self, key):
        principal = self[key]
        context = principal.context
        del context.parent[context.name]
        del self.storage[key]

    @default
    @locktree
    def __getitem__(self, key):
        key = ensure_text(key)
        try:
            return self.storage[key]
        except KeyError:
            criteria = {self._key_attr: key}
            attrlist = ['rdn', self._key_attr]
            res = self.context.search(criteria=criteria, attrlist=attrlist)
            if not res:
                raise KeyError(key)
            if len(res) > 1:  # pragma: no cover
                msg = u'More than one principal with id "{0}" found.'
                logger.warning(msg.format(key))
            prdn = res[0][1]['rdn']
            if prdn in self.context._deleted_children:
                raise KeyError(key)
            dn = res[0][0]
            path = explode_dn(dn)[:len(self.context.DN.split(',')) * -1]
            context = self.context
            for rdn in reversed(path):
                context = context[rdn]
            principal = self.principal_factory(
                context,
                attraliaser=self.principal_attraliaser
            )
            principal.__name__ = key
            principal.__parent__ = self
            self.storage[key] = principal
            return principal

    @default
    @locktree
    def __iter__(self):
        attrlist = ['rdn', self._key_attr]
        for principal in self.context.batched_search(attrlist=attrlist):
            prdn = principal[1]['rdn']
            if prdn in self.context._deleted_children:
                continue
            yield ensure_text(principal[1][self._key_attr][0])
        for principal in self.context._added_children:
            yield self.context[principal].attrs[self._key_attr]

    @default
    @locktree
    def __setitem__(self, name, value):
        if not isinstance(value, self.principal_factory):
            raise ValueError(u"Given value not instance of '{0}'".format(
                self.principal_factory.__name__
            ))
        # XXX: check if there is valid user context
        exists = False
        try:
            self[name]
            exists = True
        except KeyError:
            pass
        if exists:
            raise KeyError(
                u"Principal with id '{0}' already exists.".format(name)
            )
        value.__name__ = name
        value.__parent__ = self
        self.storage[name] = value

    @default
    @property
    def changed(self):
        return self.context.changed

    @default
    @locktree
    def invalidate(self, key=None):
        """Invalidate LDAPPrincipals.
        """
        if key is None:
            self.context.invalidate()
            self.storage.clear()
            return
        try:
            principal = self.storage[key]
            principal.context.parent.invalidate(principal.context.name)
            del self.storage[key]
        except KeyError:
            pass

    @default
    @locktree
    def __call__(self):
        self.context()

    @default
    def _alias_dict(self, dct):
        ret = dict()
        for key, val in six.iteritems(self.principal_attraliaser):
            for k, v in six.iteritems(dct):
                if val == k:
                    ret[key] = v
        return ret

    @default
    def _unalias_list(self, lst):
        unalias = self.principal_attraliaser.unalias
        return [unalias(x) for x in lst]

    @default
    def _unalias_dict(self, dct):
        if dct is None:
            return None
        unalias = self.principal_attraliaser.unalias
        unaliased_dct = dict(
            [(unalias(key), val) for key, val in six.iteritems(dct)])
        return unaliased_dct

    @default
    def raw_search(self, criteria=None, attrlist=None,
                   exact_match=False, or_search=False, or_keys=None,
                   or_values=None, page_size=None, cookie=None):
        search_attrlist = [self._key_attr]
        if attrlist is not None and self._key_attr not in attrlist:
            search_attrlist += attrlist
        try:
            results = self.context.search(
                criteria=self._unalias_dict(criteria),
                attrlist=self._unalias_list(search_attrlist),
                exact_match=exact_match,
                or_search=or_search,
                or_keys=or_keys,
                or_values=or_values,
                page_size=page_size,
                cookie=cookie
            )
        except ldap.NO_SUCH_OBJECT:  # pragma: no cover
            logger.debug("LDAPPrincipals.raw_search: ldap.NO_SUCH_OBJECT")
            return []
        if isinstance(results, tuple):
            results, cookie = results
        if attrlist is not None:
            _results = list()
            for _, att in results:
                try:
                    principal_id = att[self._key_attr][0]
                except (KeyError, IndexError):
                    continue
                aliased = self._alias_dict(att)
                for key in list(aliased.keys()):
                    if key not in attrlist:
                        del aliased[key]
                _results.append((principal_id, aliased))
            results = _results
        else:
            results = [att[self._key_attr][0] for _, att in results]
        if cookie is not None:
            return results, cookie
        return results

    @default
    def search(self, criteria=None, attrlist=None,
               exact_match=False, or_search=False):
        result = []
        cookie = ''
        while True:
            chunk, cookie = self.raw_search(
                criteria=criteria,
                attrlist=attrlist,
                exact_match=exact_match,
                or_search=or_search,
                page_size=self.context.ldap_session._props.page_size,
                cookie=cookie
            )
            result += chunk
            if not cookie:
                break
        return result

    @default
    @locktree
    def create(self, pid, **kw):
        # XXX: mechanism for defining a target container if scope is SUBTREE
        # create principal with LDAPNode as context
        context = LDAPNode()
        principal = self.principal_factory(
            context,
            attraliaser=self.principal_attraliaser
        )
        # ensure id on attributes
        kw['id'] = pid
        # avoid overwriting key attribute if given in kw
        if self._key_attr in kw:
            del kw[self._key_attr]
        # set additional attributes on principal
        for k, v in kw.items():
            principal.attrs[k] = v
        # set principal to self
        self[pid] = principal
        # if setting principal has been successful, hook up principal context
        # to ldap tree
        rdn = u'{0}={1}'.format(
            self._rdn_attr,
            principal.context.attrs[self._rdn_attr]
        )
        self.context[rdn] = context
        # return newly created principal
        return self[pid]


class LDAPUsers(LDAPPrincipals, UgmUsers):
    principal_factory = default(User)

    @override
    @locktree
    def __delitem__(self, key):
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
        context = user.context
        del context.parent[context.name]
        del self.storage[key]

    @default
    def id_for_login(self, login):
        criteria = {self._login_attr: login}
        attrlist = [self._key_attr]
        res = self.context.search(criteria=criteria, attrlist=attrlist)
        if not res:
            return ensure_text(login)
        if len(res) > 1:  # pragma: no cover
            msg = u'More than one principal with login "{0}" found.'
            logger.warning(msg.format(login))
        return ensure_text(res[0][1][self._key_attr][0])

    @default
    @debug
    def authenticate(self, login=None, pw=None, id=None):
        if id is not None:
            # bbb. deprecated usage
            login = id
        user_id = self.id_for_login(login)
        criteria = {self._key_attr: user_id}
        attrlist = ['dn']
        account_expires = self.account_expires
        if account_expires:
            attrlist.append(account_expires.attribute)
        try:
            res = self.context.search(criteria=criteria, attrlist=attrlist)
        except ldap.NO_SUCH_OBJECT:  # pragma: no cover
            return False
        if not res:
            return False
        if len(res) > 1:  # pragma: no cover
            msg = u'More than one principal with login "{0}" found.'
            logger.warning(msg.format(user_id))
        if account_expires:
            try:
                expired = account_expires.expired(res[0][1])
            except ValueError:
                # unknown expires field data
                msg = (
                    u"Accound expiration flag for user '{0}' "
                    u"contains unknown data"
                )
                logger.error(msg.format(id))
                return False
            if expired:
                return False
        user_dn = res[0][1]['dn']
        session = self.context.ldap_session
        authenticated = session.authenticate(user_dn, pw)
        return authenticated and user_id or False

    @default
    @debug
    def passwd(self, id, oldpw, newpw):
        user_id = self.id_for_login(id)
        criteria = {self._key_attr: user_id}
        attrlist = ['dn']
        if self.account_expires:
            attrlist.append(self.account_expires.attribute)
        res = self.context.search(criteria=criteria, attrlist=attrlist)
        if not res:
            raise KeyError(id)
        if len(res) > 1:  # pragma: no cover
            msg = u'More than one principal with login "{0}" found.'
            logger.warning(msg.format(user_id))
        user_dn = res[0][1]['dn']
        self.context.ldap_session.passwd(user_dn, oldpw, newpw)
        object_classes = self.context.child_defaults['objectClass']
        user_node = self[user_id].context
        user_node.attrs.load()
        if 'sambaSamAccount' in object_classes:
            user_node.attrs['sambaNTPassword'] = sambaNTPassword(newpw)
            user_node.attrs['sambaLMPassword'] = sambaLMPassword(newpw)
            user_node()


@plumbing(
    LDAPUsers,
    MappingConstraints,
    MappingAdopt,
    Attributes,
    MappingNode)
class Users(object):
    pass


def member_format(object_classes):
    for object_class in MEMBER_LOOKUP_BY_CLASS:
        if object_class in object_classes:
            return MEMBER_LOOKUP_BY_CLASS[object_class]['format']
    raise Exception(
        u"Can not lookup member format for object-classes: {0}".format(
            object_classes,
        )
    )


def member_attribute(object_classes):
    for object_class in MEMBER_LOOKUP_BY_CLASS:
        if object_class in object_classes:
            return MEMBER_LOOKUP_BY_CLASS[object_class]['attribute']
    raise Exception(
        u"Can not lookup member attribute for object-classes: {0}".format(
            object_classes,
        )
    )


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
    def __setitem__(_next, self, key, value):
        # XXX: kick this, dummy member should be created by default value
        #      callback
        if self._member_attribute not in value.attrs:
            value.attrs[self._member_attribute] = []
        if self._member_format is FORMAT_UID:
            value.attrs[self._member_attribute].insert(0, 'nobody')
        else:
            value.attrs[self._member_attribute].insert(0, 'cn=nobody')
        _next(self, key, value)


class LDAPGroups(LDAPGroupsMapping):
    principal_factory = default(Group)

    @override
    @locktree
    def __delitem__(self, key):
        key = ensure_text(key)
        group = self[key]
        parent = self.parent
        if parent and parent.rcfg is not None:
            for role in group.roles:
                group.remove_role(role)
        context = group.context
        del context.parent[context.name]
        del self.storage[key]


@plumbing(
    LDAPGroups,
    MappingConstraints,
    MappingAdopt,
    Attributes,
    MappingNode)
class Groups(object):
    pass


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
            ret.append('group:{}'.format(key))
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
                    group_members.append('group:{}'.format(groups.idbydn(dn, True)))
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
            principal = principals[key]
            ret = principal.context.DN
        elif self._member_format == FORMAT_UID:
            ret = key
        return ret

    @override
    @locktree
    def __getitem__(self, key):
        key = ensure_text(key)
        if key not in self:
            raise KeyError(key)
        principals = self.related_principals(key)
        if key.startswith('group:'):
            key = key[6:]
        return principals[key]

    @override
    @locktree
    def __delitem__(self, key):
        key = ensure_text(key)
        if key not in self:
            raise KeyError(key)
        principals = self.related_principals(key)
        if self._member_format == FORMAT_DN:
            real_key = key
            if key.startswith('group:'):
                real_key = key[6:]
            val = principals[real_key].context.DN
        elif self._member_format == FORMAT_UID:
            val = key
        # self.context.attrs[self._member_attribute].remove won't work here
        # issue in LDAPNodeAttributes, does not recognize changed this way.
        members = self.context.attrs[self._member_attribute]
        members.remove(val)
        self.context.attrs[self._member_attribute] = members
        # XXX: call here immediately?
        self.context()


@plumbing(
    LDAPRole,
    MappingConstraints,
    Attributes,
    MappingNode)
class Role(object):
    pass


class LDAPRoles(LDAPGroupsMapping):
    principal_factory = default(Role)


@plumbing(
    LDAPRoles,
    MappingConstraints,
    MappingAdopt,
    Attributes,
    MappingNode)
class Roles(object):
    pass


class LDAPUgm(UgmBase):

    @override
    def __init__(self, name=None, parent=None, props=None,
                 ucfg=None, gcfg=None, rcfg=None):
        """
        :param name: Node name.
        :param parent: Node parent.
        :param props: LDAPProps instance.
        :param ucfg: UsersConfig instance.
        :param gcfg: GroupsConfig instance.
        :param rcfg: RolesConfig instance.
        """
        # XXX: remove name and parent once using ``NodeInit`` behavior
        self.__name__ = name
        self.__parent__ = parent
        self.props = props
        self.ucfg = ucfg
        self.gcfg = gcfg
        self.rcfg = rcfg

    @override
    @locktree
    def __getitem__(self, key):
        if key not in self.storage:
            if key == 'users':
                self['users'] = Users(self.props, self.ucfg)
            elif key == 'groups':
                self['groups'] = Groups(self.props, self.gcfg)
        return self.storage[key]

    @override
    @locktree
    def __setitem__(self, key, value):
        self._chk_key(key)
        self.storage[key] = value

    @override
    def __delitem__(self, key):
        raise NotImplementedError(u"Operation forbidden on this node.")

    @override
    def __iter__(self):
        for key in ['users', 'groups']:
            yield key

    @override
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
            raise ValueError(u"Principal already has role '{}'".format(rolename))
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
            raise ValueError(u"Role not exists '{}'".format(rolename))
        if uid not in role.member_ids:
            raise ValueError(u"Principal does not has role '{}'".format(rolename))
        del role[uid]
        if not role.member_ids:
            parent = role.parent
            del parent[rolename]

    @default
    @property
    def _roles(self):
        if 'roles' not in self.storage:
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
            uid = 'group:{}'.format(uid)
        return uid

    @default
    def _chk_key(self, key):
        if key not in ['users', 'groups']:
            raise KeyError(key)


@plumbing(
    LDAPUgm,
    MappingConstraints,
    MappingAdopt,
    Attributes,
    DefaultInit,
    MappingNode,
    OdictStorage)
class Ugm(object):

    def invalidate(self, key=None):
        if key is None:
            self.storage.clear()
            return
        del self.storage[key]
