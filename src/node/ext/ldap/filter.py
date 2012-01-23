# -*- coding: utf-8 -*-
from node.ext.ldap.base import encode_utf8


class LDAPFilter(object):
    
    def __init__(self, queryFilter=None):
        if queryFilter is not None \
                and not isinstance(queryFilter, basestring) \
                and not isinstance(queryFilter, LDAPFilter):
            raise TypeError('Query filter must be LDAPFilter or string')
        queryFilter = encode_utf8(queryFilter)
        self._filter = queryFilter
        if isinstance(queryFilter, LDAPFilter):
            self._filter = str(queryFilter)

    def __and__(self, other):
        if other is None:
            return self
        res = ''
        if isinstance(other, LDAPFilter):
            other = str(other)
        elif not isinstance(other, basestring):
            raise TypeError(u"unsupported operand type")
        us = str(self)
        if us and other:
            res = '(&%s%s)' % (us, other)
        elif us:
            res = us
        elif other:
            res = other
        return LDAPFilter(res)

    def __or__(self, other):
        if other is None:
            return self
        res = ''
        if isinstance(other, LDAPFilter):
            other = str(other)
        elif not isinstance(other, basestring):
            raise TypeError(u"unsupported operand type")
        us = str(self)
        if us and other:
            res = '(|%s%s)' % (us, other)
        return LDAPFilter(res)

    def __contains__(self, attr):
        attr = '(%s=' % (attr,)
        return attr in self._filter

    def __str__(self):
        return self._filter and self._filter or ''

    def __repr__(self):
        return "LDAPFilter('%s')" % (self._filter,)


class LDAPDictFilter(LDAPFilter):
    
    def __init__(self, criteria, or_search=False):
        self.criteria = criteria
        self.or_search = or_search

    def __str__(self):
        if not self.criteria:
            return ''
        return str(dict_to_filter(self.criteria, self.or_search))

    def __repr__(self):
        return "LDAPDictFilter(criteria=%r)" % (self.criteria,)


class LDAPRelationFilter(LDAPFilter):
    
    def __init__(self, node, relation, or_search=True):
        self.relation = relation
        self.gattrs = node.attrs
        self.or_search = or_search

    def __str__(self):
        """turn relation string into ldap filter string
        """
        _filter = LDAPFilter()
        dictionary = dict()
        
        parsedRelation = dict()
        for pair in self.relation.split('|'):
            k, _, v = pair.partition(':')
            if not k in parsedRelation:
                parsedRelation[k] = list()
            parsedRelation[k].append(v)

        existing = [k for k in self.gattrs]
        for k, vals in parsedRelation.items():
            for v in vals:
                if str(v) == '' \
                  or str(k) == '' \
                  or str(k) not in existing:
                    continue
                dictionary[str(v)] = self.gattrs[str(k)]

        self.dictionary = dictionary

        if len(dictionary) is 1:
            _filter = LDAPFilter(self.relation)
        else:
            _filter = dict_to_filter(parsedRelation, self.or_search)

        return self.dictionary and \
            str(dict_to_filter(self.dictionary, self.or_search)) or ''
    
    def __repr__(self):
        return "LDAPRelationFilter('%s')" % (str(self),)


def dict_to_filter(criteria, or_search):
    """Turn dictionary criteria into ldap queryFilter string
    """
    _filter = None
    for attr, values in criteria.items():
        attr = encode_utf8(attr)
        if not isinstance(values, list):
            values = [values]
        for value in values:
            if isinstance(value, unicode):
                value = encode_utf8(value)
            if _filter is None:
                _filter = LDAPFilter('(%s=%s)' % (attr, value))
            else:
                _next = '(%s=%s)' % (attr, value)
                if or_search:
                    _filter |= _next
                else:
                    _filter &= _next
    if _filter is None:
        _filter = LDAPFilter()
    return _filter