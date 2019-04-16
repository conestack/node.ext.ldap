# -*- coding: utf-8 -*-
from node.ext.ldap.base import ensure_bytes_py2
import six


# all special characters except * are escaped, that means * can be
# used to perform suffix/prefix/contains searches, monkey-patch if you
# don't like
ESCAPE_CHARS = {
    # '*': '\\2a',
    '(': '\\28',
    ')': '\\29',
    '/': '\\2f',
    '\\': '\\5c',
    '\x00': '\\00',
}

string_type = basestring if six.PY2 else str


class LDAPFilter(object):

    def __init__(self, queryFilter=None):
        if queryFilter is not None \
                and not isinstance(queryFilter, string_type) \
                and not isinstance(queryFilter, LDAPFilter):
            raise TypeError('Query filter must be LDAPFilter or string')
        queryFilter = ensure_bytes_py2(queryFilter)
        self._filter = queryFilter
        if isinstance(queryFilter, LDAPFilter):
            self._filter = str(queryFilter)

    def __and__(self, other):
        if other is None:
            return self
        res = ''
        if isinstance(other, LDAPFilter):
            other = str(other)
        elif not isinstance(other, string_type):
            raise TypeError('unsupported operand type')
        us = str(self)
        if us and other:
            res = '(&{}{})'.format(us, other)
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
        elif not isinstance(other, string_type):
            raise TypeError('unsupported operand type')
        us = str(self)
        if us and other:
            res = '(|{}{})'.format(us, other)
        return LDAPFilter(res)

    def __contains__(self, attr):
        return self._filter.find('({}='.format(attr)) > -1

    def __str__(self):
        return self._filter and self._filter or ''

    def __repr__(self):
        return "LDAPFilter('{}')".format(self._filter)


class LDAPDictFilter(LDAPFilter):

    def __init__(self, criteria, or_search=False,
                 or_keys=None, or_values=None):
        self.criteria = criteria
        self.or_search = or_search
        self.or_keys = or_keys
        self.or_values = or_values

    def __str__(self):
        if not self.criteria:
            return ''
        return str(dict_to_filter(
            self.criteria,
            or_search=self.or_search,
            or_keys=self.or_keys,
            or_values=self.or_values
        ))

    def __repr__(self):
        cr = [
            "'{}': '{}'".format(ensure_bytes_py2(k), ensure_bytes_py2(v))
            for k, v in sorted(self.criteria.items())
        ]
        return 'LDAPDictFilter(criteria={{{}}})'.format(', '.join(cr))


class LDAPRelationFilter(LDAPFilter):

    def __init__(self, node, relation, or_search=True):
        self.relation = relation
        self.gattrs = node.attrs
        self.or_search = or_search

    def __str__(self):
        """turn relation string into ldap filter string
        """
        dictionary = dict()
        parsedRelation = dict()
        for pair in self.relation.split('|'):
            k, _, v = pair.partition(':')
            if k not in parsedRelation:
                parsedRelation[k] = list()
            parsedRelation[k].append(v)
        existing = [x for x in self.gattrs]
        for k, vals in parsedRelation.items():
            for v in vals:
                if (str(v) == '' or str(k) == '' or str(k) not in existing):
                    continue
                dictionary[str(v)] = self.gattrs[str(k)]
        self.dictionary = dictionary
        if self.dictionary:
            return str(dict_to_filter(self.dictionary, self.or_search))
        return ''

    def __repr__(self):
        return "LDAPRelationFilter('{}')".format(str(self))


def dict_to_filter(criteria, or_search=False, or_keys=None, or_values=None):
    """Turn dictionary criteria into ldap queryFilter string
    """
    or_keys = (or_keys is None) and or_search or or_keys
    or_values = (or_values is None) and or_search or or_values
    _filter = None
    for attr, values in sorted(criteria.items()):
        attr = ensure_bytes_py2(attr)
        if not isinstance(values, list):
            values = [values]
        attrfilter = None
        for value in values:
            value = ensure_bytes_py2(value)
            attr = ''.join([ESCAPE_CHARS.get(x, x) for x in attr])
            if isinstance(value, str):
                value = ''.join([ESCAPE_CHARS.get(x, x) for x in value])
            valuefilter = LDAPFilter('({}={})'.format(attr, value))
            if attrfilter is None:
                attrfilter = valuefilter
                continue
            if or_values:
                attrfilter |= valuefilter
            else:
                attrfilter &= valuefilter
        if _filter is None:
            _filter = attrfilter
            continue
        if or_keys:
            _filter |= attrfilter
        else:
            _filter &= attrfilter
    if _filter is None:
        _filter = LDAPFilter()
    return _filter
