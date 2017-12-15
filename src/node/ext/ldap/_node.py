# -*- coding: utf-8 -*-
from ldap import INVALID_DN_SYNTAX
from ldap import MOD_ADD
from ldap import MOD_DELETE
from ldap import MOD_REPLACE
from ldap import NO_SUCH_OBJECT
from ldap.functions import explode_dn
from node.behaviors import Adopt
from node.behaviors import Attributes
from node.behaviors import AttributesLifecycle
from node.behaviors import Lifecycle
from node.behaviors import NodeAttributes
from node.behaviors import NodeChildValidate
from node.behaviors import Nodespaces
from node.behaviors import Nodify
from node.behaviors import OdictStorage
from node.ext.ldap import BASE
from node.ext.ldap import LDAPSession
from node.ext.ldap import ONELEVEL
from node.ext.ldap.events import LDAPNodeAddedEvent
from node.ext.ldap.events import LDAPNodeCreatedEvent
from node.ext.ldap.events import LDAPNodeDetachedEvent
from node.ext.ldap.events import LDAPNodeModifiedEvent
from node.ext.ldap.events import LDAPNodeRemovedEvent
from node.ext.ldap.filter import LDAPDictFilter
from node.ext.ldap.filter import LDAPFilter
from node.ext.ldap.filter import LDAPRelationFilter
from node.ext.ldap.interfaces import ILDAPStorage
from node.ext.ldap.schema import LDAPSchemaInfo
from node.interfaces import IInvalidate
from node.utils import CHARACTER_ENCODING
from node.utils import debug
from node.utils import decode
from node.utils import encode
from plumber import Behavior
from plumber import default
from plumber import finalize
from plumber import plumb
from plumber import plumbing
from zope.deprecation import deprecated
from zope.interface import implementer


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
        # nothing to load
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
            raise RuntimeError(                            #pragma NO COVERAGE
                u"Fatal. Expected entry does not exist "   #pragma NO COVERAGE
                u"or more than one entry found"            #pragma NO COVERAGE
            )                                              #pragma NO COVERAGE
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


# B/C
AttributesBehavior = LDAPAttributesBehavior
deprecated('AttributesBehavior', """
``node.ext.ldap._node.AttributesBehavior`` is deprecated as of node.ext.ldap
1.0 and will be removed in node.ext.ldap 1.1. Use
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

        :param name: Initial base DN for the root LDAP Node.
        :param props: ``node.ext.ldap.LDAPProps`` instance.
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
        self._reload = False
        self._multivalued_attributes = set()
        self._binary_attributes = set()
        self._page_size = 1000
        if props:
            # only at root node
            self._ldap_session = LDAPSession(props)
            self._ldap_session.baseDN = self.DN
            self._ldap_schema_info = LDAPSchemaInfo(props)
            self._multivalued_attributes = props.multivalued_attributes
            self._binary_attributes = props.binary_attributes
            self._page_size = props.page_size
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
        if not isinstance(val, LDAPNode):
            # create one from whatever we got
            # XXX: raise KeyError instead of trying to create node
            val = self._create_suitable_node(val)
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
        rdn, rdn_val = key.split('=')
        if rdn not in val.attrs:
            val._notify_suppress = True
            val.attrs[rdn] = rdn_val
            val._notify_suppress = False
        self.storage[key] = val
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
        # value not persistent yet, remove from storage and add list
        if key in self._added_children:
            del self.storage[key]
            self._added_children.remove(key)
            self.changed = False
            return
        val = self[key]
        val._action = ACTION_DELETE
        # this will also trigger the changed chain
        val.changed = True
        self._deleted_children.add(key)

    @finalize
    def __iter__(self):
        if self.name is None:
            return
        cookie = ''
        while True:
            try:
                res = self.ldap_session.search(
                    scope=ONELEVEL,
                    baseDN=encode(self.DN),
                    attrlist=[''],
                    page_size=self._page_size,
                    cookie=cookie,
                )
            except NO_SUCH_OBJECT:
                # happens if not persisted yet
                res = list()
            if isinstance(res, tuple):
                res, cookie = res
            for dn, _ in res:
                key = decode(explode_dn(dn)[0])
                # do not yield if node is supposed to be deleted
                if key not in self._deleted_children:
                    yield key
            if not cookie:
                break

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
        dn = self.DN.encode('ascii', 'replace') or '(dn not set)'
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
        # For one and the same entry, ldap will always return the same DN.
        # However, depending on the individual syntax definition of the DN's
        # components there might be a multitude of strings that equal the same
        # DN, e.g. for cn:
        #     'cn=foo bar' == 'cn=foo   bar' -> True
        if self.parent:
            return self.parent.child_dn(self.name)
        if self.name:
            # We should not have a name if we are not a root node.
            return decode(self.name)
        return u''

    @default
    @property
    def rdn_attr(self):
        return self.name and self.name.split('=')[0] or None

    @property
    def changed(self):
        return self._changed

    @default
    @changed.setter
    def changed(self, value):
        """Set the changed flag.

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

    @default
    def child_dn(self, key):
        # return child DN for key
        if self._dn:
            return u','.join([decode(key), decode(self._dn)])
        return u','.join([decode(key), decode(self.name)])

    @default
    @property
    def exists(self):
        try:
            res = self.ldap_session.search(
                scope=BASE,
                baseDN=self.DN.encode('utf-8'),
                attrlist=['']
            )
            # this probably never happens
            if len(res) != 1:
                raise RuntimeError()                        #pragma NO COVERAGE
            return True
        except NO_SUCH_OBJECT:
            return False

    @default
    def node_by_dn(self, dn, strict=False):
        """Return node from tree by DN.
        """
        root = node = self.root
        base_dn = root.name
        if not dn.endswith(base_dn):
            raise ValueError(u'Invalid base DN')
        dn = dn[:len(dn) - len(base_dn)].strip(',')
        for rdn in reversed(explode_dn(encode(dn))):
            try:
                node = node[rdn]
            except KeyError:
                if strict:
                    raise ValueError(u'Tree contains no node by given DN. '
                                     u'Failed at RDN {}'.format(rdn))
                return None
        return node

    @default
    @debug
    def search(self, queryFilter=None, criteria=None, attrlist=None,
               relation=None, relation_node=None, exact_match=False,
               or_search=False, or_keys=None, or_values=None,
               page_size=None, cookie=None, get_nodes=False):
        attrset = set(attrlist or [])
        attrset.discard('dn')
        attrset.discard('rdn')
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
        # check exact match
        if exact_match and len(matches) > 1:
            raise ValueError(u"Exact match asked but result not unique")
        if exact_match and len(matches) == 0:
            raise ValueError(u"Exact match asked but result length is zero")
        # extract key and desired attributes
        res = []
        for dn, attrs in matches:
            dn = decode(dn)
            if attrlist is not None:
                resattr = dict()
                for k, v in attrs.iteritems():
                    if k in attrlist:
                        # Check binary binary attribute directly from root
                        # data to avoid initing attrs for a simple search.
                        if k in self.root._binary_attributes:
                            resattr[decode(k)] = v
                        else:
                            resattr[decode(k)] = decode(v)
                if 'dn' in attrlist:
                    resattr[u'dn'] = dn
                if 'rdn' in attrlist:
                    rdn = explode_dn(encode(dn))[0]
                    resattr[u'rdn'] = decode(rdn)
                if get_nodes:
                    res.append((self.node_by_dn(dn, strict=True), resattr))
                else:
                    res.append((dn, resattr))
            else:
                if get_nodes:
                    res.append(self.node_by_dn(dn, strict=True))
                else:
                    res.append(dn)
        if cookie is not None:
            return (res, cookie)
        return res

    @default
    def batched_search(self, page_size=None, search_func=None, **kw):
        """Search generator function which does paging for us.
        """
        if page_size is None:
            page_size = self.ldap_session._props.page_size
        if search_func is None:
            search_func = self.search
        matches = []
        cookie = None
        kw['page_size'] = page_size
        while True:
            kw['cookie'] = cookie
            matches, cookie = search_func(**kw)
            for item in matches:
                yield item
            if not cookie:
                break

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
        'created': LDAPNodeCreatedEvent,
        'added': LDAPNodeAddedEvent,
        'modified': LDAPNodeModifiedEvent,
        'removed': LDAPNodeRemovedEvent,
        'detached': LDAPNodeDetachedEvent,
    }
