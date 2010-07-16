# XXX: This could be moved to its own egg

LDAP_CHARACTER_ENCODING='utf8'

class StrCodec(object):
    """Encode unicodes to strs and decode strs to unicodes

    We will recursively work on arbitrarily nested structures consisting of
    str, unicode, list, tuple and dict mixed with others, which we won't touch.
    During that process a deep copy is produces leaving the orginal data
    structure intact.
    """
    def __init__(self,encoding=LDAP_CHARACTER_ENCODING):
        self._encoding = encoding

    def encode(self, arg):
        """Return an encoded copy of the argument
        - strs are decoded and reencode to make sure they conform to the
          encoding
        - unicodes are encoded as str according to encoding
        - lists/tuples/dicts are recursively worked on
        - everything else is left untouched
        """
        if isinstance(arg, (list, tuple)):
            arg = arg.__class__(map(self.encode, arg))
        elif isinstance(arg, dict):
            arg = dict(
                [self.encode(t) for t in arg.iteritems()]
                )
        elif isinstance(arg, str):
            arg = self.encode(
                    self.decode(arg)
                    )
        elif isinstance(arg, unicode):
            arg = arg.encode(self._encoding)
        return arg

    def decode(self, arg):
        if isinstance(arg, (list, tuple)):
            arg = arg.__class__(map(self.decode, arg))
        elif isinstance(arg, dict):
            arg = dict(
                [self.decode(t) for t in arg.iteritems()]
                )
        elif isinstance(arg, str):
            arg = arg.decode(self._encoding)
        return arg

# make one global encoder available + convenience methods
strcodec = StrCodec()
encode = strcodec.encode
decode = strcodec.decode
