# -*- coding: utf-8 -*-
try:
    from zope.app.event.objectevent import objectEventNotify # BBB
except ImportError, e:
    from zope.component.event import objectEventNotify
from odict import odict
from zope.interface import implements
from plumber import (
    plumber,
    Part,
    plumb,
    default,
    finalize,
)
from node.parts import (
    Nodespaces,
    Attributes,
    NodeAttributes,
    Lifecycle,
    AttributesLifecycle,
    NodeChildValidate,
    Adopt,
    UnicodeAware,
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
from node.ext.ldap import (
    BASE,
    ONELEVEL,
    LDAPSession,
)
from node.ext.ldap.base import escape
from node.ext.ldap.interfaces import ILDAPStorage
from node.ext.ldap.events import (
    LDAPNodeCreatedEvent,
    LDAPNodeAddedEvent,
    LDAPNodeModifiedEvent,
    LDAPNodeRemovedEvent,
    LDAPNodeDetachedEvent
)    
from node.ext.ldap.filter import (
    LDAPFilter,
    LDAPDictFilter,
    LDAPRelationFilter,
)
from node.ext.ldap.schema import LDAPSchemaInfo
from ldap.functions import explode_dn
from ldap import (
    MOD_ADD,
    MOD_DELETE,
    MOD_REPLACE,
)

ACTION_ADD = 0
ACTION_MODIFY = 1
ACTION_DELETE = 2


class AttributesPart(Part):
    
    @plumb
    def __init__(_next, self, name=None, parent=None):
        _next(self, name=name, parent=parent)
        self.load()
        
    
    @default
    def load(self):
        if not self.parent.name \
          or not self.parent.ldap_session \
          or self.parent._action == ACTION_ADD:
            return
        
        self.clear()
        
        attrlist = ['*']
        
        # XXX: operational attributes
        #if self.session._props.operationalAttributes:
        #    attrlist.append('+')
        
        # XXX: if memberOf support enabled
        #if self.session._props.memberOfSupport:
        #    attrlist.append('memberOf')
        
        # fetch our node with all attributes
        entry = self.parent.ldap_session.search(
                scope=BASE,
                baseDN=self.parent.DN,
                force_reload=self.parent._reload,
                attrlist=attrlist,
                )
        
        if len(entry) != 1:
            raise RuntimeError(                             #pragma NO COVERAGE
                u"Fatal. Expected entry does not exist or " #pragma NO COVERAGE
                u"more than one entry found")               #pragma NO COVERAGE
        
        attrs = entry[0][1]
        for key, item in attrs.items():
            if len(item) == 1 and not self.is_multivalued(key):
                self[key] = item[0]
            else:
                self[key] = item
        
        # superclass' __setitem__ set our changed flag. We just loaded from
        # ldap and are not changed.
        self.changed = False
        if self.parent._action not in [ACTION_ADD, ACTION_DELETE]:
            self.parent._action = None
            self.parent.changed = False
    
    @plumb
    def __setitem__(_next, self, key, val):
        _next(self, key, val)
        self._set_attrs_modified()

    @plumb
    def __delitem__(_next, self, key):
        _next(self, key)
        self._set_attrs_modified()
    
    @default
    def _set_attrs_modified(self):
        self.changed = True
        if self.parent._action not in [ACTION_ADD, ACTION_DELETE]:
            self.parent._action = ACTION_MODIFY
            self.parent.changed = True
        
    @default    
    def is_binary(self, name):
        return name in self.parent.root._binary_attributes

    @default    
    def is_multivalued(self, name):
        return name in self.parent.root._multivalued_attributes


class LDAPNodeAttributes(NodeAttributes):
    __metaclass__ = plumber
    __plumbing__ = (
        UnicodeAware,
        AttributesPart,
        AttributesLifecycle,
    )


class LDAPStorage(OdictStorage):
    """
    XXX: only use ``self.storage`` to store real values, ``self._keys` should
         only contain ``True`` or ``False``
    """
    
    implements(ILDAPStorage, IInvalidate)
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
        self._ldap_session = None
        self._changed = False
        self._action = None
        self._seckey_attrs = None
        self._reload = False
        self._init_keys()
        if props:
            # only at root node
            self._ldap_session = LDAPSession(props)
            self._ldap_session.baseDN = self.DN
            self._ldap_schema_info = LDAPSchemaInfo(props)
            self._multivalued_attributes = props.multivalued_attributes
            self._binary_attributes = props.binary_attributes

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
        """Here nodes are created for keys, if they do not exist already
        """
        if isinstance(key, str):
            key = decode(key)
        if not self._keys:
            self._load_keys()
        if self._keys[key] is not None:
            return self.storage[key]
        val = self.child_factory()
        val._ldap_session = self.ldap_session
        val.__name__ = key
        val.__parent__ = self
        self.storage[key] = self._keys[key] = val
        return val

    @finalize
    def __setitem__(self, key, val):
        if isinstance(key, str):
            key = decode(key)
        
        # XXX: scope is search scope, why not add children?
        #      feels like trying to add security the wrong place
        #if self.search_scope is BASE:
        #    raise NotImplementedError(
        #        u"Seriously? Adding with scope == BASE?")
        
        if self._key_attr != 'rdn' and self._rdn_attr is None:
            raise RuntimeError(
                u"Adding with key != rdn needs _rdn_attr to be set.")
        if not isinstance(val, LDAPNode):
            # create one from whatever we got
            val = self._create_suitable_node(val)
        
        # At this point we need to have an LDAPNode as val
        if self._key_attr != 'rdn':
            val.attrs[self._key_attr] = key
            if val.attrs.get(self._rdn_attr) is None:
                raise ValueError(
                    u"'%s' needed in node attributes for rdn." % \
                        (self._rdn_attr,))
        else:
            # set rdn attr if not present
            rdn, rdn_val = key.split('=')
            if not rdn in val.attrs:
                val._notify_suppress = True
                val.attrs[rdn] = rdn_val
                val._notify_suppress = False
        
        val.__name__ = key
        val.__parent__ = self
        val._ldap_session = self.ldap_session
        
        if self._keys is None:
            self._load_keys()
        try:
            # a value with key is already in the directory
            self._keys[key]
        except KeyError:
            # the value is not yet in the directory
            val._action = ACTION_ADD
            val.changed = True
            self.changed = True
        
        self.storage[key] = val
        self._keys[key] = val
        
        if self._key_attr == 'rdn':
            rdn = key
        else:
            rdn = '%s=%s' % (self._rdn_attr, val.attrs[self._rdn_attr])
        self._child_dns[key] = ','.join((rdn, self.DN))
        
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
        """Do not delete immediately. Just mark LDAPNode to be deleted and
        remove key from self._keys.
        """
        if isinstance(key, str):
            key = decode(key)
        val = self[key]
        val._action = ACTION_DELETE
        # this will also trigger the changed chain
        val.changed = True
        del self._keys[key]
        try:
            self._deleted.append(val)
        except AttributeError:
            self._deleted = list()
            self._deleted.append(val)
    
    @finalize
    def __iter__(self):
        """This is where keys are retrieved from ldap
        """
        if self.name is None:
            return iter(list())
        if self._reload:
            self._init_keys()
        if self._keys is None and self._action != ACTION_ADD:
            self._load_keys()
        try:
            return self._keys.__iter__()
        except Exception:
            return iter(list())

    @finalize
    def __call__(self):
        if self.changed and self._action is not None:
            if self._action == ACTION_ADD:
                self._ldap_add()
            elif self._action == ACTION_MODIFY:
                self._ldap_modify()
            elif self._action == ACTION_DELETE:
                self._ldap_delete()
            try:
                self.nodespaces['__attrs__'].changed = False
            except KeyError:
                pass
            self.changed = False
            self._action = None
        if self._keys is None:
            return
        for node in self._keys.values() + getattr(self, '_deleted', []):
            if node is not None and node.changed:
                node()

    @finalize
    def __repr__(self):
        # Doctest fails if we output utf-8
        try:
            dn = self.DN.encode('ascii', 'replace') or '(dn not set)'
        except KeyError, e:
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
    
    # This is really ldap
    @default
    @property
    def DN(self):
        """
        ATTENTION: For one and the same entry, ldap will always return
        the same DN. However, depending on the individual syntax
        definition of the DN's components there might be a multitude
        of strings that equal the same DN, e.g. for cn:
           'cn=foo bar' == 'cn=foo   bar' -> True
        """
        if self.parent is not None:
            return self.parent.child_dn(self.name)
        elif self.name is not None:
            # We should not have a name if we are not a root node.
            return self.name
        else:
            return u''
    
    @default
    @property
    def rdn_attr(self):
        """XXX: only tested on LDAPNode, might not work in UGM
        """
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
        if value:
            # Setting is easy
            self._changed = True
        else:
            # Unsetting needs more checks
            try:
                if self.nodespaces['__attrs__'].changed:
                    return
            except KeyError:
                # No attributes loaded, yet - cannot be changed
                pass
            childs = getattr(self, '_deleted', [])
            if self._keys is not None:
                childs.extend(
                    filter(lambda x: x is not None, self._keys.values()))
            for child in childs:
                if child.changed:
                    return
            self._changed = False
        # And propagate to parent
        if self._changed is not oldval and self.parent is not None:
            self.parent.changed = self._changed

    changed = default(property(_get_changed, _set_changed))

    # This is really ldap
    @default
    def child_dn(self, key):
        return self._child_dns[key]

    @default
    @debug
    def search(self, queryFilter=None, criteria=None, attrlist=None, 
               relation=None, relation_node=None, exact_match=False, 
               or_search=False):
        attrset = set(attrlist or [])
        attrset.discard('dn')
        # fetch also the key attribute
        if not self._key_attr == 'rdn':
            attrset.add(self._key_attr)
        
        # XXX: Make this work for string queries and move to LDADCommunicator
        #if self.ldap_session._props.escape_queries:
        #    if criteria is not None:
        #        for key, val in criteria.items():
        #            criteria[key] = escape(val)
        
        # Create queryFilter from all filter definitions
        # filter for this search ANDed with the default filters defined on self
        search_filter = LDAPFilter(queryFilter)
        search_filter &= LDAPDictFilter(criteria, or_search=or_search)
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
            baseDN=self.DN,
            force_reload=self._reload,
            attrlist=list(attrset)
        )
        
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
                resattr = dict([(k,v) for k,v in attrs.iteritems()
                        if k in attrlist])
                if 'dn' in attrlist:
                    resattr['dn'] = dn
                res.append((key, resattr))
            else:
                res.append(key)
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
            - if child in self._keys, check if child has changed
            - if changed, raise RuntimeError
            - if not changed, remove item from self.storage and set
              self._keys[key] to None, which forces it to be reloaded.
        """
        if key is None:
            if self.changed:
                raise RuntimeError(u"Invalid tree state. Try to invalidate "
                                   u"changed node.")
            self.storage.clear()
            self.attrs.load()
            self._init_keys()
            self._reload = True
            return
        try:
            child = self._keys[key]
            if child is not None:
                if child.changed:
                    raise RuntimeError(
                        u"Invalid tree state. Try to invalidate "
                        u"changed child node '%s'." % (key,))
                del self.storage[key]
                self._keys[key] = None
        except KeyError:
            pass
    
    #@finalize
    #def sort(self, cmp=None, key=None, reverse=False):
    #    # XXX: a sort working only on the keys could work without wakeup -->
    #    # sortonkeys()
    #    #  first wake up all entries
    #    dummy = self.items()
    #    if not dummy:
    #        return
    #    # second sort them
    #    import pdb;pdb.set_trace()
    #    self._keys.sort(cmp=cmp, key=key, reverse=reverse)
    
    @default
    def _init_keys(self):
        # the _keys is None or an odict.
        # if an odict, the value is either None or the value
        # None means, the value wasnt loaded
        self._keys = None
        self._seckeys = None
        self._child_dns = None

    @default
    def _load_keys(self):
        self._keys = odict()
        self._child_dns = {}
        attrlist = ['dn']
        if self._seckey_attrs:
            self._seckeys = dict()
            attrlist.extend(self._seckey_attrs)
        for key, attrs in self.search(attrlist=attrlist):
            try:
                self._keys[key]
            except KeyError:
                self._keys[key] = None
                self._child_dns[key] = attrs['dn']
                for seckey_attr, seckey in \
                        self._calculate_seckeys(attrs).items():
                    try:
                        self._seckeys[seckey_attr]
                    except KeyError:
                        self._seckeys[seckey_attr] = {}
                    try:
                        self._seckeys[seckey_attr][seckey]
                    except KeyError:
                        self._seckeys[seckey_attr][seckey] = key
                    else:
                        # XXX: ever reached?
                        raise KeyError(
                            u"Secondary key not unique: %s='%s'." % \
                                    (seckey_attr, seckey))
            else:
                raise RuntimeError(u"Key not unique: %s='%s'." % \
                        (self._key_attr, key))
    
    # a keymapper
    @default
    def _calculate_key(self, dn, attrs):
        if self._key_attr == 'rdn':
            # explode_dn is ldap world
            key = decode(explode_dn(encode(dn))[0])
        else:
            key = attrs[self._key_attr]
            if isinstance(key, list):
                if len(key) != 1:
                    msg = u"Expected one value for '%s' " % (self._key_attr,)
                    msg += u"not %s: '%s'." % (len(key), key)
                    raise KeyError(msg)
                key = key[0]
        return key

    # secondary keys
    @default
    def _calculate_seckeys(self, attrs):
        if not self._seckey_attrs:
            return {}
        seckeys = {}
        for seckey_attr in self._seckey_attrs:
            try:
                seckey = attrs[seckey_attr]
            except KeyError:
                # no sec key found, skip
                continue
            else:
                if isinstance(seckey, list):
                    if len(seckey) != 1:
                        msg = u"Expected one value for '%s' " % (seckey_attr,)
                        msg += "not %s: '%s'." %(len(seckey), seckey)
                        raise KeyError(msg)
                    seckey = seckey[0]
                seckeys[seckey_attr] = seckey
        return seckeys
    
    @default
    def _create_suitable_node(self, vessel):
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
        """adds self to the ldap directory.
        """
        self.ldap_session.add(self.DN, self.attrs)

    @default
    def _ldap_modify(self):
        """modifies attributs of self on the ldap directory.
        """
        modlist = list()
        orgin = self.attributes_factory(name='__attrs__', parent=self)
        
        for key in orgin:
            # MOD_DELETE
            if not key in self.attrs:
                moddef = (MOD_DELETE, key, None)
                modlist.append(moddef)
        for key in self.attrs:
            # MOD_ADD
            if key not in orgin:
                moddef = (MOD_ADD, key, self.attrs[key])
                modlist.append(moddef)
            # MOD_REPLACE
            elif self.attrs[key] != orgin[key]:
                moddef = (MOD_REPLACE, key, self.attrs[key])
                modlist.append(moddef)
        if modlist:
            self.ldap_session.modify(self.DN, modlist)

    @default
    def _ldap_delete(self):
        """delete self from the ldap-directory.
        """
        self.parent._keys[self.name] = None
        del self.parent.storage[self.name]
        del self.parent._keys[self.name]
        self.ldap_session.delete(self.DN)

    @default
    @property
    def schema_info(self):
        if self.parent is not None:
            return self.root._ldap_schema_info
        return self._ldap_schema_info

class LDAPNode(object):
    __metaclass__ = plumber
    __plumbing__ = (
        Nodespaces,
        Attributes,
        Lifecycle,
        NodeChildValidate,
        Adopt,
        Nodify,
        LDAPStorage,
    )
    
    events = {
        'created':  LDAPNodeCreatedEvent,
        'added':    LDAPNodeAddedEvent,
        'modified': LDAPNodeModifiedEvent,
        'removed':  LDAPNodeRemovedEvent,
        'detached': LDAPNodeDetachedEvent,
    }
