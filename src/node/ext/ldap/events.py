# -*- coding: utf-8 -*-
from zope.interface import implementer
from node.events import (
    NodeCreatedEvent,
    NodeAddedEvent,
    NodeModifiedEvent,
    NodeRemovedEvent,
    NodeDetachedEvent,
)
from .interfaces import (
    ILDAPNodeCreatedEvent,
    ILDAPNodeAddedEvent,
    ILDAPNodeModifiedEvent,
    ILDAPNodeRemovedEvent,
    ILDAPNodeDetachedEvent,
)


@implementer(ILDAPNodeCreatedEvent)
class LDAPNodeCreatedEvent(NodeCreatedEvent):
    pass


@implementer(ILDAPNodeAddedEvent)
class LDAPNodeAddedEvent(NodeAddedEvent):
    pass


@implementer(ILDAPNodeModifiedEvent)
class LDAPNodeModifiedEvent(NodeModifiedEvent):
    pass


@implementer(ILDAPNodeRemovedEvent)
class LDAPNodeRemovedEvent(NodeRemovedEvent):
    pass


@implementer(ILDAPNodeDetachedEvent)
class LDAPNodeDetachedEvent(NodeDetachedEvent):
    pass
