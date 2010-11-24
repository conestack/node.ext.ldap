from zope.interface import implements
try:
    from node.aliasing import (
            DictAliaser,
            AliasedNodespace,
            )
    from node.base import AbstractNode
except ImportError:
    node = __import__('node.aliasing', {})
    node = __import__('node.base', {})
    DictAliaser = node.aliasing.DictAliaser
    AliasedNodespace = node.aliasing.AliasedNodespace
    AbstractNode = node.base.AbstractNode

from zodict import AttributedNode

from bda.ldap import LDAPProps, LDAPNode
from bda.ldap import BASE, ONELEVEL, SUBTREE
from bda.ldap.debug import debug
from bda.ldap.interfaces import ILDAPUsersConfig
from bda.ldap.interfaces import ILDAPGroupsConfig


class Principal(AbstractNode):
    """Turns a node into a principal
    """
    def __init__(self, context, attraliaser=None):
        self.context = context
        self.attraliaser = attraliaser

    @property
    def id(self):
        return self.__name__

    @property
    def attrs(self):
        if self.attraliaser is None:
            return self.context.attrs
        return AliasedNodespace(self.context.attrs, self.attraliaser)

    def __repr__(self):
        return "<%s '%s'>" % (
                self.__class__.__name__.split('.')[-1],
                unicode(self.id).encode('ascii', 'replace'),
                )

    def __iter__(self):
        return iter([])


class User(Principal):
    """Turns a node into a user
    """
    @property
    def login(self):
        return self.attrs['login']

    def authenticate(self, pw):
        return bool(self.__parent__.authenticate(id=self.id, pw=pw))

    def passwd(self, oldpw, newpw):
        self.__parent__.passwd(id=self.id, oldpw=oldpw, newpw=newpw)


class Group(Principal):
    """Turns a node into a group
    """


class Principals(AbstractNode):
    """Turn a nodespace into a source of principals

    XXX: Should be based on a LazyNode to cache principal objects
    """
    principals_factory = None

    def __init__(self, context, principal_attrmap=None):
        self.context = context
        # XXX: it seems currently an aliaser is needed any way, is that good?
        self.principal_attrmap = principal_attrmap
        self.principal_attraliaser = DictAliaser(principal_attrmap)

    @property
    def __name__(self):
        return self.context.__name__

    # principals have ids
    @property
    def ids(self):
        return self.context.keys

    def __delitem__(self, key):
        del self.context[key]

    def __getitem__(self, key):
        # XXX: should use lazynodes caching, for now:
        # users['foo'] is not users['foo']
        principal = self.principal_factory(
                self.context[key],
                attraliaser=self.principal_attraliaser
                )
        principal.__name__ = self.context[key].__name__
        principal.__parent__ = self
        return principal

    def __iter__(self):
        return self.context.__iter__()

    def __setitem__(self, name, vessel):
        try:
            attrs = vessel.nodespaces['__attrs__']
        except KeyError:
            raise ValueError(u"Attributes need to be set.")

        nextvessel = AttributedNode()
        nextvessel.__name__ = name
        nextvessel.attribute_access_for_attrs = False
        principal = self.principal_factory(
                nextvessel,
                attraliaser=self.principal_attraliaser
                )
        principal.__name__ = name
        principal.__parent__ = self
        # XXX: we could cache here, given that we are based on a LazyNode or
        # similar
        for key, val in attrs.iteritems():
            principal.attrs[key] = val
        self.context[name] = nextvessel

    def _alias_dict(self, dct):
        if dct is None:
            return None
        alias = self.principal_attraliaser.alias
        aliased_dct = dict(
                [(alias(key), val) for key, val in dct.iteritems()]
                )
        return aliased_dct

    def _unalias_list(self, lst):
        if lst is None:
            return None
        unalias = self.principal_attraliaser.unalias
        return [unalias(x) for x in lst]

    def _unalias_dict(self, dct):
        if dct is None:
            return None
        unalias = self.principal_attraliaser.unalias
        unaliased_dct = dict(
                [(unalias(key), val) for key, val in dct.iteritems()]
                )
        return unaliased_dct

    def search(self, criteria=None, attrlist=None, exact_match=False,
            or_search=False):
        # XXX: stripped down for now, compare to LDAPNode.search
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


class LDAPPrincipalsConfig(object):
    """Superclass for LDAPUsersConfig and LDAPGroupsConfig
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


class LDAPUsersConfig(LDAPPrincipalsConfig):
    """Define how users look and where they are
    """
    implements(ILDAPUsersConfig)
    
    #when a user is modified, killed etc an event is emmited. To grab it you must:
    #zope.component.provideHandler(funct_to_be_executed,[1st_arg_objecttype,2nd_arg_objecttype,..])


class LDAPGroupsConfig(LDAPPrincipalsConfig):
    """Define how groups look and where they are
    """
    implements(ILDAPGroupsConfig)


class LDAPPrincipals(Principals):
    """Superclass for LDAPUsers and LDAPGroups
    """
    def __init__(self, props, cfg):
        context = LDAPNode(name=cfg.baseDN, props=props)
        super(LDAPPrincipals, self).__init__(context, cfg.attrmap)
        self.context._child_filter = cfg.queryFilter
        self.context._child_scope = cfg.scope
        self.context._child_objectClasses = cfg.objectClasses
        self.context._key_attr = cfg.attrmap['id']
        self.context._rdn_attr = cfg.attrmap['rdn']


class LDAPUsers(LDAPPrincipals):
    """Manage LDAP users
    """
    principal_factory = User

    def __init__(self, props, cfg):
        super(LDAPUsers, self).__init__(props, cfg)
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


class LDAPGroups(LDAPPrincipals):
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
