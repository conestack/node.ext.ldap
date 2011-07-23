import logging
import sys
logger = logging.getLogger('node.ext.ldap')


#XXX: why is the debug decorator restricted?
#     normally ``@debug`` should be enough. Once this decorator is more generic,
#     move to ``node.utils``


WHAT_TO_DEBUG = set([
    'authentication',
    'searching',
])


class debug:
    """Decorator which helps to control what aspects of a program to debug
    on per-function basis. Aspects are provided as list of arguments.
    It DOESN'T slowdown functions which aren't supposed to be debugged.
    """
    def __init__(self, aspects=None):
        self.aspects = set(aspects)

    def __call__(self, f): 
        if self.aspects & WHAT_TO_DEBUG:
            def newf(*args, **kws):
                logger.debug('%s: args=%s, kws=%s', f.func_name, args, kws)
                f_result = f(*args, **kws)
                logger.debug('%s: --> %s', f.func_name, f_result)
                return f_result
            newf.__doc__ = f.__doc__
            return newf
        else:
            return f