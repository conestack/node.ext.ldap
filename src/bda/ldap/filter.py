from ldap.filter import filter_format

class LDAPFilter(object):
    def __init__(self, queryFilter=None):
        # We expect queryFilter to be correctly escaped
        self._filter = queryFilter

    def __and__(self, other):
        if other is None:
            return self
        res = ''
        if isinstance(other, LDAPFilter):
            other = other.__str__()
        elif not isinstance(other, basestring):
            raise TypeError(u"unsupported operand type")
        us = self.__str__()
        if us and other:
            res = '(&%s%s)' % (us, other)
        elif us:
            res = us
        elif other:
            res = other
        return LDAPFilter(res)

    def __contains__(self, attr):
        attr = '(%s=' % (attr,)
        return attr in self._filter

    def __str__(self):
        return self._filter and self._filter or ''

    def __repr__(self):
        return "LDAPFilter('%s')" % (self._filter,)


class LDAPDictFilter(LDAPFilter):
    def __init__(self, criteria):
        self.criteria = criteria

    def __str__(self):
        return self.criteria and dict_to_filter(self.criteria).__str__() or ''

    def __repr__(self):
        return "LDAPDictFilter(criteria=%r)" % (self.criteria,)


def dict_to_filter(criteria):
    """Turn dictionary criteria into ldap queryFilter string
    """
    _filter = LDAPFilter()
    for attr, values in criteria.items():
        if not isinstance(values, list):
            values = [values]
        for value in values:
            _filter &= '(%s=%s)' % (attr, value)
    return _filter
