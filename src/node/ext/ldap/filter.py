# -*- coding: utf-8 -*-
from .base import decode_utf8
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


class LDAPFilter(object):

    def __init__(self, queryFilter=None):
        if queryFilter is not None \
                and not isinstance(queryFilter, six.string_types) \
                and not isinstance(queryFilter, LDAPFilter):
            raise TypeError('Query filter must be LDAPFilter or string')
        self._filter = queryFilter
        if isinstance(queryFilter, LDAPFilter):
            self._filter = str(queryFilter)
            if six.PY2:
                self._filter = self._filter.decode('utf-8')

    def __and__(self, other):
        if other is None:
            return self
        res = ''
        if isinstance(other, LDAPFilter):
            other = str(other)
            if six.PY2:
                other = other.decode('utf-8')
        elif not isinstance(other, six.string_types):
            raise TypeError(u"unsupported operand type")
        us = str(self)
        if six.PY2:
            us = us.decode('utf-8')
        if us and other:
            res = u'(&%s%s)' % (us, other)
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
            if six.PY2:
                other = other.decode('utf-8')
        elif not isinstance(other, six.string_types):
            raise TypeError(u"unsupported operand type")
        us = str(self)
        if six.PY2:
            us = us.decode('utf-8')
        if us and other:
            res = u'(|%s%s)' % (us, other)
        return LDAPFilter(res)

    def __contains__(self, attr):
        return self._filter.find('({}='.format(attr)) > -1

    def __str__(self):
        filterstr = self._filter and self._filter or ''
        if six.PY2:
            filterstr = filterstr.encode('utf-8')
        return filterstr

    def __repr__(self):
        filterstr = self._filter
        if six.PY2 and isinstance(filterstr, six.string_types):
            filterstr = filterstr.encode('utf-8')
        return "LDAPFilter('%s')" % (filterstr,)


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
        return str(dict_to_filter(self.criteria,
                                  or_search=self.or_search,
                                  or_keys=self.or_keys,
                                  or_values=self.or_values))

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
                if (str(v) == '' or
                    str(k) == '' or
                    str(k) not in existing):
                    continue
                dictionary[str(v)] = self.gattrs[str(k)]
        self.dictionary = dictionary
        if self.dictionary:
            return str(dict_to_filter(self.dictionary, self.or_search))
        return ''

    def __repr__(self):
        return "LDAPRelationFilter('%s')" % (str(self),)


def dict_to_filter(criteria, or_search=False, or_keys=None, or_values=None):
    """Turn dictionary criteria into ldap queryFilter string
    """
    or_keys = (or_keys is None) and or_search or or_keys
    or_values = (or_values is None) and or_search or or_values
    _filter = None
    for attr, values in criteria.items():
        attr = decode_utf8(attr)
        if not isinstance(values, list):
            values = [values]
        attrfilter = None
        for value in values:
            attr = ''.join([ESCAPE_CHARS.get(x, x) for x in attr])
            if isinstance(value, six.string_types):
                value = ''.join([ESCAPE_CHARS.get(x, x) for x in value])
            if isinstance(value, six.binary_type):
                value = decode_utf8(value)
            valuefilter = LDAPFilter('(%s=%s)' % (attr, value))
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
