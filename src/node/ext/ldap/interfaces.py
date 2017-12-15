# -*- coding: utf-8 -*-
from node.interfaces import INodeAddedEvent
from node.interfaces import INodeCreatedEvent
from node.interfaces import INodeDetachedEvent
from node.interfaces import INodeModifiedEvent
from node.interfaces import INodeRemovedEvent
from node.interfaces import IStorage
from zope.interface import Attribute
from zope.interface import Interface


class ICacheProviderFactory(Interface):
    """Create some ICacheProvider implementing object on __call__.

    Must be registered as utility.
    """
    def __call__():
        """See above.
        """


class ILDAPProps(Interface):
    """LDAP properties configuration interface.
    """

    uri = Attribute('LDAP URI')

    user = Attribute('LDAP User')

    password = Attribute('Bind Password')

    cache = Attribute('Flag wether to use cache or not')

    timeout = Attribute('Timeout in seconds')

    start_tls = Attribute('TLS enabled')

    ignore_cert = Attribute('Ignore TLS/SSL certificate errors')

    tls_cacertfile = Attribute('Name of CA Cert file')

    # XXX
    # tls_cacertdir = Attribute('Path to CA Cert directory')

    # XXX
    # tls_clcertfile = Attribute('Name of CL Cert file')

    # XXX
    # tls_clkeyfile = Attribute('Path to CL key file')

    retry_max = Attribute('Retry count')

    retry_delay = Attribute('Retry delay in seconds')

    multivalued_attributes = Attribute('Attributes considered multi valued')

    binary_attributes = Attribute('Attributes considered binary')

    page_size = Attribute('Page size for LDAP queries.')


class ILDAPPrincipalsConfig(Interface):
    """LDAP principals configuration interface.
    """

    baseDN = Attribute('Principals base DN')

    attrmap = Attribute('Principals Attribute map as ``odict.odict``')

    scope = Attribute('Search scope for principals')

    queryFilter = Attribute('Search Query filter for principals')

    # XXX
    # member_relation = Attribute('Optional member relation to be used to '
    #                             'speed up groups search, i.e. '
    #                             ''uid:memberUid'')

    objectClasses = Attribute('Object classes for new principals.')

    defaults = Attribute(
        'Dict like object containing default values for principal creation.'
        'A value could either be static or a callable. This defaults take'
        'precedence to defaults detected via set object classes.'
    )

    strict = Attribute(
        'Flag whether to initialize Aliaser for LDAP attributes in strict '
        'mode. Defaults to True.'
    )

    memberOfSupport = Attribute(
        'Flag whether to use "memberOf" attribute (AD) or memberOf overlay '
        '(openldap) for Group membership resolution where appropriate.'
    )

    # XXX: currently expiresAttr only gets considered for user authentication
    #      group and role expiration is not implemented yet.
    expiresAttr = Attribute(
        'Attribute containing an expiration timestamp from epoch in UTC. '
        'If None, entry never expires.'
    )

    expiresUnit = Attribute(
        'Expiration unit. Either ``node.ext.ldap.ugm.EXPIRATION_DAYS`` or '
        '``EXPIRATION_SECONDS``. Defaults to days.'
    )


class ILDAPUsersConfig(ILDAPPrincipalsConfig):
    """LDAP users configuration interface.
    """


class ILDAPGroupsConfig(ILDAPPrincipalsConfig):
    """LDAP groups configuration interface.
    """


class ILDAPStorage(IStorage):
    """A LDAP Node.
    """

    ldap_session = Attribute('``node.ext.ldap.session.LDAPSession`` instance.')

    DN = Attribute('LDAP object DN.')

    rdn_attr = Attribute('RDN attribute name.')

    changed = Attribute('Flag whether node has been modified.')

    search_scope = Attribute('Default child search scope')

    search_filter = Attribute('Default child search filter')

    search_criteria = Attribute('Default child search criteria')

    search_relation = Attribute('Default child search relation')

    child_factory = Attribute('Factory used for child node instanciation.')

    child_defaults = Attribute(
        'Default child attributes. Will be set to all children attributes'
        'on ``__setitem__`` if not present yet.'
    )

    def child_dn(key):
        """Return child DN for ``key``.

        :param key: Child key.
        """

    def search(queryFilter=None, criteria=None, attrlist=None,
               relation=None, relation_node=None, exact_match=False,
               or_search=False, or_keys=None, or_values=None,
               page_size=None, cookie=None, get_nodes=False):
        """Search the directors.

        All search criteria are additive and will be ``&``ed. ``queryFilter``
        and ``criteria`` further narrow down the search space defined by
        ``self.search_filter``, ``self.search_criteria`` and
        ``self.search_relation``.

        The search result is a list of matching keys if ``attrlist`` is None,
        otherwise a list of 2-tuples containing (key, attrdict). If
        ``get_nodes`` is True, the result is either a list of nodes or a list
        of 2-tuples containing (node, attrdict).

        :param queryFilter: LDAP queryFilter, e.g. ``(objectClass=foo)``, as
            string or ``LDAPFilter`` instance.
        :param criteria: Dictionary of attribute value(s) (string or list of
            string)
        :param attrlist: Normally a list of keys is returned. By defining
            attrlist the return format will be
            ``[(key, {attr1: [value1, ...]}), ...]``. To get this format
            without any attributs, i.e. empty dicts in the tuples, specify an
            empty attrlist. In addition to the normal LDAP attributes you can
            also the request the DN to be included. DN is also the only value
            in result set as string instead of list.
        :param relation: The nodes we search has a relation to us. A relation
            is defined as a string of attribute pairs
            ``<relation> = '<our_attr>:<child_attr>'``. The value of these
            attributes must match for relation to match. Multiple pairs can be
            or-joined with.
        :param relation_node: Node instance used to create the relation filter.
            If not defined, ``self`` is used.
        :param exact_match: Raise ``ValueError`` if not one match, return
            format is a single key or tuple, if attrlist is specified.
        :param or_search: Flag whether criteria should be OR-ed or AND-ed.
            Defaults to False.
        :param or_keys: Flag whether criteria keys should be OR-ed or AND-ed.
            Overrides and defaults to ``or_search``.
        :param or_values: Flag whether criteria values should be OR-ed or
            AND-ed. Overrides and defaults to ``or_search``.
        :param page_size: LDAP pagination search size.
        :param cookie: LDAP pagination search cookie.
        :param get_nodes: Flag whether to return LDAP nodes in search result.
        :return result: If no page size defined, return value is the result,
            otherwise a tuple containing (cookie, result).
        """


###############################################################################
# events
###############################################################################


class ILDAPNodeCreatedEvent(INodeCreatedEvent):
    """new LDAP node was born.
    """


class ILDAPNodeAddedEvent(INodeAddedEvent):
    """LDAP node has been added to its parent.
    """


class ILDAPNodeModifiedEvent(INodeModifiedEvent):
    """LDAP node has been modified.
    """


class ILDAPNodeRemovedEvent(INodeRemovedEvent):
    """LDAP node has been removed from its parent.
    """


class ILDAPNodeDetachedEvent(INodeDetachedEvent):
    """LDAP node has been detached from its parent.
    """
