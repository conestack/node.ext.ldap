# -*- coding: utf-8 -*-
from ldap import (
    MOD_ADD,
    MOD_DELETE,
    MOD_REPLACE,
    NO_SUCH_OBJECT,
    INVALID_DN_SYNTAX,
)
from ldap.functions import explode_dn
from zope.interface import implementer
from zope.deprecation import deprecated
from plumber import (
    plumbing,
    Behavior,
    plumb,
    default,
    finalize,
)
from node.behaviors import (
    Nodespaces,
    Attributes,
    NodeAttributes,
    Lifecycle,
    AttributesLifecycle,
    NodeChildValidate,
    Adopt,
    Nodify,
    OdictStorage,
)
from node.utils import (
    encode,
    decode,
    CHARACTER_ENCODING,
    debug,
)
from node.interfaces import IInvalidate
from . import (
    BASE,
    ONELEVEL,
    LDAPSession,
)
from .interfaces import ILDAPStorage
from .events import (
    LDAPNodeCreatedEvent,
    LDAPNodeAddedEvent,
    LDAPNodeModifiedEvent,
    LDAPNodeRemovedEvent,
    LDAPNodeDetachedEvent
)
from .filter import (
    LDAPFilter,
    LDAPDictFilter,
    LDAPRelationFilter,
)
from .schema import LDAPSchemaInfo


ACTION_ADD = 0
ACTION_MODIFY = 1
ACTION_DELETE = 2


class LDAPAttributesBehavior(Behavior):

    @plumb
    def __init__(_next, self, name=None, parent=None):
        _next(self, name=name, parent=parent)
        self.load()

    @default
    def load(self):
        ldap_node = self.parent
        # nothong to load
        if not ldap_node.name \
                or not ldap_node.ldap_session \
                or ldap_node._action == ACTION_ADD:
            return
        # clear in case reload
        self.clear()
        # query all attributes
        attrlist = ['*']

        # XXX: operational attributes
        # if self.session._props.operationalAttributes:
        #    attrlist.append('+')

        # XXX: if memberOf support enabled
        # if self.session._props.memberOfSupport:
        #    attrlist.append('memberOf')

        # fetch attributes for ldap_node
        entry = ldap_node.ldap_session.search(
            scope=BASE,
            baseDN=ldap_node.DN.encode('utf-8'),
            force_reload=ldap_node._reload,
            attrlist=attrlist,
        )
        # result length must be 1
        if len(entry) != 1:
            raise RuntimeError(                            # pragma NO COVERAGE
                u"Fatal. Expected entry does not exist "   # pragma NO COVERAGE
                u"or more than one entry found"            # pragma NO COVERAGE
            )                                              # pragma NO COVERAGE
        # read attributes from result and set to self
        attrs = entry[0][1]
        for key, item in attrs.items():
            if len(item) == 1 and not self.is_multivalued(key):
                self[key] = item[0]
            else:
                self[key] = item
        # __setitem__ has set our changed flag. We just loaded from LDAP, so
        # unset it
        self.changed = False
        # node has been modified prior to (re)loading attributes, so unset
        # markers there too
        if ldap_node._action not in [ACTION_ADD, ACTION_DELETE]:
            # remove ldap node key from parent modified list if present
            # need to do this before setting changed to false, otherwise
            # setting changed flag gets ignored.
            if ldap_node.parent:
                ldap_node.parent._modified_children.remove(ldap_node.name)
            ldap_node._action = None
            ldap_node.changed = False

    @plumb
    def __setitem__(_next, self, key, val):
        if not self.is_binary(key):
            val = decode(val)
        key = decode(key)
        _next(self, key, val)
        self._set_attrs_modified()

    @plumb
    def __delitem__(_next, self, key):
        _next(self, key)
        self._set_attrs_modified()

    @default
    def _set_attrs_modified(self):
        ldap_node = self.parent
        self.changed = True
        if ldap_node._action not in [ACTION_ADD, ACTION_DELETE]:
            ldap_node._action = ACTION_MODIFY
            ldap_node.changed = True
            if ldap_node.parent:
                ldap_node.parent._modified_children.add(ldap_node.name)

    @default
    def is_binary(self, name):
        return name in self.parent.root._binary_attributes

    @default
    def is_multivalued(self, name):
        return name in self.parent.root._multivalued_attributes


AttributesPart = LDAPAttributesBehavior  # B/C
deprecated('AttributesPart', """
``node.ext.ldap._node.AttributesPart`` is deprecated as of node.ext.ldap 0.9.4
and will be removed in node.ext.ldap 1.0. Use
``node.ext.ldap._node.LDAPAttributesBehavior`` instead.""")


@plumbing(
    LDAPAttributesBehavior,
    AttributesLifecycle)
class LDAPNodeAttributes(NodeAttributes):
    """Attributes for LDAPNode.
    """


@implementer(ILDAPStorage, IInvalidate)
class LDAPStorage(OdictStorage):
    attributes_factory = finalize(LDAPNodeAttributes)

    @finalize
    def __init__(self, name=None, props=None):
        """LDAP Node expects ``name`` and ``props`` arguments for the root LDAP
        Node or nothing for children.

        name
            Initial base DN for the root LDAP Node.

        props
            ``node.ext.ldap.LDAPProps`` object.
        """
        if (name and not props) or (props and not name):
            raise ValueError(u"Wrong initialization.")
        if name and not isinstance(name, unicode):
            name = name.decode(CHARACTER_ENCODING)
        self.__name__ = name
        self.__parent__ = None
        self._dn = None
        self._ldap_session = None
        self._changed = False
        self._action = None
        self._added_children = set()
        self._modified_children = set()
        self._deleted_children = set()
        self._seckey_attrs = None
        self._reload = False
        self._multivalued_attributes = {}
        self._binary_attributes = {}
        if props:
            # only at root node
            self._ldap_session = LDAPSession(props)
            self._ldap_session.baseDN = self.DN
            self._ldap_schema_info = LDAPSchemaInfo(props)
            self._multivalued_attributes = props.multivalued_attributes
            self._binary_attributes = props.binary_attributes
            self._check_duplicates = props.check_duplicates

        # XXX: make them public
        self._key_attr = 'rdn'
        self._rdn_attr = None

        # search related defaults
        self.search_scope = ONELEVEL
        self.search_filter = None
        self.search_criteria = None
        self.search_relation = None

        # creation related default
        self.child_factory = LDAPNode
        self.child_defaults = None

    @finalize
    def __getitem__(self, key):
        # nodes are created for keys, if they do not already exist in memory
        if isinstance(key, str):
            key = decode(key)
        try:
            return self.storage[key]
        except KeyError:
            val = self.child_factory()
            val.__name__ = key
            val.__parent__ = self
            try:
                res = self.ldap_session.search(
                    scope=BASE,
                    baseDN=val.DN.encode('utf-8'),
                    attrlist=[''],  # no need for attrs
                )
                # remember DN
                val._dn = res[0][0]
                val._ldap_session = self.ldap_session
                self.storage[key] = val
                return val
            except (NO_SUCH_OBJECT, INVALID_DN_SYNTAX):
                raise KeyError(key)

    @finalize
    def __setitem__(self, key, val):
        if isinstance(key, str):
            key = decode(key)

        if self._key_attr != 'rdn' and self._rdn_attr is None:
            raise RuntimeError(
                u"Adding with key != rdn needs _rdn_attr to be set.")
        if not isinstance(val, LDAPNode):
            # create one from whatever we got
            val = self._create_suitable_node(val)

        # at this point we need to have an LDAPNode as val
        if self._key_attr != 'rdn':
            val.attrs[self._key_attr] = key
            if val.attrs.get(self._rdn_attr) is None:
                raise ValueError(
                    u"'{0}' needed in node attributes for rdn.".format(
                        self._rdn_attr
                    )
                )
        else:
            # set rdn attr if not present
            rdn, rdn_val = key.split('=')
            if rdn not in val.attrs:
                val._notify_suppress = True
                val.attrs[rdn] = rdn_val
                val._notify_suppress = False

        val.__name__ = key
        val.__parent__ = self
        val._dn = self.child_dn(key)
        val._ldap_session = self.ldap_session

        try:
            self.ldap_session.search(
                scope=BASE,
                baseDN=val.DN.encode('utf-8'),
                attrlist=[''],  # no need for attrs
            )
        except (NO_SUCH_OBJECT, INVALID_DN_SYNTAX):
            # the value is not yet in the directory
            val._action = ACTION_ADD
            val.changed = True
            self.changed = True
            self._added_children.add(key)

        self.storage[key] = val

        # if self._key_attr == 'rdn':
        #     rdn = key
        # else:
        #     rdn = '%s=%s' % (self._rdn_attr, val.attrs[self._rdn_attr])
        # self._child_dns[key] = ','.join((rdn, self.DN))

        if self.child_defaults:
            for k, v in self.child_defaults.items():
                if k in val.attrs:
                    # skip default if attribute already exists
                    continue
                if callable(v):
                    v = v(self, key)
                val.attrs[k] = v

    @finalize
    def __delitem__(self, key):
        # do not delete immediately. Just mark LDAPNode to be deleted.
        if isinstance(key, str):
            key = decode(key)
        val = self[key]
        val._action = ACTION_DELETE
        # this will also trigger the changed chain
        val.changed = True
        self._deleted_children.add(key)

    @finalize
    def __iter__(self):
        if self.name is None:
            return
        attrlist = ['dn']
#         if self._seckey_attrs:
#             self._seckeys = dict()
#             attrlist.extend(self._seckey_attrs)
        try:
            res = self.search(attrlist=attrlist)
        # happens if not persisted yet
        except NO_SUCH_OBJECT:
            res = list()
        for key, attrs in res:
#             self._keys[key] = False
#             self._child_dns[key] = attrs['dn']
#             for seckey_attr, seckey in self._calculate_seckeys(attrs).items():
#                 try:
#                     self._seckeys[seckey_attr]
#                 except KeyError:
#                     self._seckeys[seckey_attr] = {}
#                 try:
#                     self._seckeys[seckey_attr][seckey]
#                 except KeyError:
#                     self._seckeys[seckey_attr][seckey] = key
#                 else:
#                     if not self._check_duplicates:
#                         continue
# 
#                     raise KeyError(
#                         u"Secondary key not unique: {0}='{1}'.".format(
#                             seckey_attr, seckey
#                         )
#                     )
            # do not yield if node is supposed to be deleted
            if key not in self._deleted_children:
                yield key
        # also yield keys of children not persisted yet.
        for key in self._added_children:
            yield key

    @finalize
    def __call__(self):
        if self.changed and self._action is not None:
            if self._action == ACTION_ADD:
                self.parent._added_children.remove(self.name)
                self._ldap_add()
            elif self._action == ACTION_MODIFY:
                if self.parent:
                    self.parent._modified_children.remove(self.name)
                self._ldap_modify()
            elif self._action == ACTION_DELETE:
                self.parent._deleted_children.remove(self.name)
                self._ldap_delete()
            try:
                self.nodespaces['__attrs__'].changed = False
            except KeyError:
                pass
            self.changed = False
            self._action = None
        deleted = [self[key] for key in self._deleted_children]
        for node in self.storage.values() + deleted:
            if node.changed:
                node()

    @finalize
    def __repr__(self):
        # Doctest fails if we output utf-8
        try:
            dn = self.DN.encode('ascii', 'replace') or '(dn not set)'
        except KeyError:
            dn = '(dn not available yet)'
        if self.parent is None:
            return "<%s - %s>" % (dn, self.changed)
        name = self.name.encode('ascii', 'replace')
        return "<%s:%s - %s>" % (dn, name, self.changed)

    __str__ = finalize(__repr__)

    @finalize
    @property
    def noderepr(self):
        return repr(self)

    @default
    @property
    def ldap_session(self):
        return self._ldap_session

    @default
    @property
    def DN(self):
        # ATTENTION: For one and the same entry, ldap will always return
        # the same DN. However, depending on the individual syntax
        # definition of the DN's components there might be a multitude
        # of strings that equal the same DN, e.g. for cn:
        #    'cn=foo bar' == 'cn=foo   bar' -> True
        if self.parent:
            return self.parent.child_dn(self.name)
        if self.name:
            # We should not have a name if we are not a root node.
            return decode(self.name)
        return u''

    @default
    @property
    def rdn_attr(self):
        # XXX: only tested on LDAPNode, might not work in UGM
        return self.name and self.name.split('=')[0] or None

    def _get_changed(self):
        return self._changed

    def _set_changed(self, value):
        """Set/Unset the changed flag

        Set:
            - if self.attrs are changed (attrs set us)
            - if a child is changed / added / removed (child sets us)
        Unset:
            - if neither a child nor the own attrs are changed (attrs or child
              tries to unset us)
        Anyway:
            - tell our parent in case we changed state
        """
        # only get active, if new state differs from old state
        oldval = self._changed
        if value is oldval:
            return
        # setting is easy
        if value:
            self._changed = True
        # unsetting needs more checks
        else:
            # check whether children are added, modified or deleted, cannot
            # unset changed state if so
            if len(self._added_children) \
                    or len(self._modified_children) \
                    or len(self._deleted_children):
                return
            # check whether attributes has changed, cannot unset changed if so
            try:
                # access attrs nodespace directly to avoid recursion error
                if self.nodespaces['__attrs__'].changed:
                    return
            # No attributes loaded yet, ignore
            except KeyError:
                pass
            # finally unset changed flag
            self._changed = False
        # propagate to parent
        if self._changed is not oldval and self.parent is not None:
            self.parent.changed = self._changed

    changed = default(property(_get_changed, _set_changed))

    @default
    def child_dn(self, key):
        # return child DN for key
        if self._dn:
            return u','.join([decode(key), decode(self._dn)])
        return u','.join([decode(key), decode(self.name)])

    @default
    @debug
    def search(self, queryFilter=None, criteria=None, attrlist=None,
               relation=None, relation_node=None, exact_match=False,
               or_search=False, or_keys=None, or_values=None,
               page_size=None, cookie=None):
        attrset = set(attrlist or [])
        attrset.discard('dn')

        # fetch also the key attribute
        if not self._key_attr == 'rdn':
            attrset.add(self._key_attr)

        # Create queryFilter from all filter definitions
        # filter for this search ANDed with the default filters defined on self
        search_filter = LDAPFilter(queryFilter)
        search_filter &= LDAPDictFilter(criteria,
                                        or_search=or_search,
                                        or_keys=or_keys,
                                        or_values=or_values,
                                        )
        _filter = LDAPFilter(self.search_filter)
        _filter &= LDAPDictFilter(self.search_criteria)
        _filter &= search_filter

        # relation filters
        if relation_node is None:
            relation_node = self
        relations = [relation, self.search_relation]
        for relation in relations:
            if not relation:
                continue
            if isinstance(relation, LDAPRelationFilter):
                _filter &= relation
            else:
                _filter &= LDAPRelationFilter(relation_node, relation)

        # XXX: Is it really good to filter out entries without the key attr or
        # would it be better to fail? (see also __iter__ secondary key)
        if self._key_attr != 'rdn' and self._key_attr not in _filter:
            _filter &= '(%s=*)' % (self._key_attr,)

        # perform the backend search
        matches = self.ldap_session.search(
            str(_filter),
            self.search_scope,
            baseDN=encode(self.DN),
            force_reload=self._reload,
            attrlist=list(attrset),
            page_size=page_size,
            cookie=cookie,
            )
        if type(matches) is tuple:
            matches, cookie = matches

        # XXX: Is ValueError appropriate?
        # XXX: why do we need to fail at all? shouldn't this be about
        # substring vs equality match?
        if exact_match and len(matches) > 1:
            raise ValueError(u"Exact match asked but result not unique")
        if exact_match and len(matches) == 0:
            raise ValueError(u"Exact match asked but result length is zero")

        # extract key and desired attributes
        res = []
        for dn, attrs in matches:
            key = self._calculate_key(dn, attrs)
            if attrlist is not None:
                resattr = dict()
                for k, v in attrs.iteritems():
                    if k in attrlist:
                        if self.attrs.is_binary(k):
                            resattr[decode(k)] = v
                        else:
                            resattr[decode(k)] = decode(v)
                if 'dn' in attrlist:
                    resattr[u'dn'] = decode(dn)
                res.append((key, resattr))
            else:
                res.append(key)
        if cookie is not None:
            return (res, cookie)
        return res

    @default
    def invalidate(self, key=None):
        """Invalidate LDAP node.

        If key is None:
            - check if self is changed
            - if changed, raise RuntimeError
            - reload self.attrs
            - set self._reload to True. This reloads the keys forcing cache
              reload as well.

        If key is given:
            - if changed, raise RuntimeError
            - if not changed, remove item from self.storage.
        """
        if key is None:
            if self.changed:
                raise RuntimeError(u"Invalid tree state. Try to invalidate "
                                   u"changed node.")
            self.storage.clear()
            self.attrs.load()
            # XXX: needs to get unset again somwhere
            self._reload = True
            return
        try:
            child = self.storage[key]
            if child.changed:
                raise RuntimeError(
                    u"Invalid tree state. Try to invalidate "
                    u"changed child node '%s'." % (key,))
            del self.storage[key]
        except KeyError:
            pass

#     @default
#     def _init_keys(self):
#         # the _keys is None or an odict.
#         # if an odict, the value is either None or the value
#         # None means, the value wasnt loaded
#         self._keys = None
#         self._seckeys = None
#         self._child_dns = None
# 
#     @default
#     def _load_keys(self):
#         self._keys = odict()
#         self._child_dns = {}
#         attrlist = ['dn']
#         if self._seckey_attrs:
#             self._seckeys = dict()
#             attrlist.extend(self._seckey_attrs)
#         for key, attrs in self.search(attrlist=attrlist):
#             try:
#                 self._keys[key]
#             except KeyError:
#                 self._keys[key] = False
#                 self._child_dns[key] = attrs['dn']
#                 for seckey_attr, seckey in \
#                         self._calculate_seckeys(attrs).items():
#                     try:
#                         self._seckeys[seckey_attr]
#                     except KeyError:
#                         self._seckeys[seckey_attr] = {}
#                     try:
#                         self._seckeys[seckey_attr][seckey]
#                     except KeyError:
#                         self._seckeys[seckey_attr][seckey] = key
#                     else:
#                         if not self._check_duplicates:
#                             continue
# 
#                         raise KeyError(
#                             u"Secondary key not unique: {0}='{1}'.".format(
#                                 seckey_attr, seckey
#                             )
#                         )
#             else:
#                 if not self._check_duplicates:
#                     continue
# 
#                 raise RuntimeError(
#                     u"Key not unique: {0}='{1}' (you may want to disable "
#                     u"check_duplicates)".format(
#                         self._key_attr, key
#                     )
#                 )

    @default
    def _calculate_key(self, dn, attrs):
        # a keymapper
        if self._key_attr == 'rdn':
            # explode_dn is ldap world
            key = explode_dn(encode(dn))[0]
        else:
            key = attrs[self._key_attr]
            if isinstance(key, list):
                if len(key) != 1:
                    msg = u"Expected one value for '%s' " % (self._key_attr,)
                    msg += u"not %s: '%s'." % (len(key), key)
                    raise KeyError(msg)
                key = key[0]
        return decode(key)

#     @default
#     def _calculate_seckeys(self, attrs):
#         # secondary keys
#         if not self._seckey_attrs:
#             return {}
#         seckeys = {}
#         for seckey_attr in self._seckey_attrs:
#             try:
#                 seckey = attrs[seckey_attr]
#             except KeyError:
#                 # no sec key found, skip
#                 continue
#             else:
#                 if isinstance(seckey, list):
#                     if len(seckey) != 1:
#                         msg = u"Expected one value for '%s' " % (seckey_attr,)
#                         msg += "not %s: '%s'." % (len(seckey), seckey)
#                         raise KeyError(msg)
#                     seckey = seckey[0]
#                 seckeys[seckey_attr] = seckey
#         return seckeys

    @default
    def _create_suitable_node(self, vessel):
        # convert vessel node to LDAPNode
        try:
            attrs = vessel.attrs
        except AttributeError:
            raise ValueError(u"No attributes found on vessel, cannot convert")
        node = LDAPNode()
        for key, val in attrs.iteritems():
            node.attrs[key] = val
        return node

    @default
    def _ldap_add(self):
        # adds self to the ldap directory.
        attrs = {}
        for key, value in self.attrs.items():
            if not self.attrs.is_binary(key):
                value = encode(value)
            attrs[encode(key)] = value
        self.ldap_session.add(encode(self.DN), attrs)

    @default
    def _ldap_modify(self):
        # modifies attributs of self on the ldap directory.
        modlist = list()
        orgin = self.attributes_factory(name='__attrs__', parent=self)

        for key in orgin:
            # MOD_DELETE
            if key not in self.attrs:
                moddef = (MOD_DELETE, encode(key), None)
                modlist.append(moddef)
        for key in self.attrs:
            # MOD_ADD
            value = self.attrs[key]
            if not self.attrs.is_binary(key):
                value = encode(value)
            if key not in orgin:
                moddef = (MOD_ADD, encode(key), value)
                modlist.append(moddef)
            # MOD_REPLACE
            elif self.attrs[key] != orgin[key]:
                moddef = (MOD_REPLACE, encode(key), value)
                modlist.append(moddef)
        if modlist:
            self.ldap_session.modify(encode(self.DN), modlist)

    @default
    def _ldap_delete(self):
        # delete self from the ldap-directory.
        del self.parent.storage[self.name]
        self.ldap_session.delete(encode(self.DN))

    @default
    @property
    def schema_info(self):
        if self.parent is not None:
            return self.root._ldap_schema_info
        return self._ldap_schema_info


@plumbing(
    Nodespaces,
    Attributes,
    Lifecycle,
    NodeChildValidate,
    Adopt,
    Nodify,
    LDAPStorage)
class LDAPNode(object):
    events = {
        'created':  LDAPNodeCreatedEvent,
        'added':    LDAPNodeAddedEvent,
        'modified': LDAPNodeModifiedEvent,
        'removed':  LDAPNodeRemovedEvent,
        'detached': LDAPNodeDetachedEvent,
    }
