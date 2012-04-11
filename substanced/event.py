from zope.interface import implementer

from .interfaces import (
    IObjectAddedEvent,
    IObjectWillBeAddedEvent,
    IObjectRemovedEvent,
    IObjectWillBeRemovedEvent,
    IObjectModifiedEvent,
    )
    
class _ObjectEvent(object):
    def __init__(self, object, parent, name):
        self.object = object
        self.parent = parent
        self.name = name

@implementer(IObjectAddedEvent)
class ObjectAddedEvent(_ObjectEvent):
    pass

@implementer(IObjectWillBeAddedEvent)
class ObjectWillBeAddedEvent(_ObjectEvent):
    pass

class _ObjectRemovalEvent(object):
    def __init__(self, object, parent, name, moving=False):
        self.object = object
        self.parent = parent
        self.name = name
        self.moving = moving

@implementer(IObjectRemovedEvent)
class ObjectRemovedEvent(_ObjectRemovalEvent):
    pass

@implementer(IObjectWillBeRemovedEvent)
class ObjectWillBeRemovedEvent(_ObjectRemovalEvent):
    pass

@implementer(IObjectModifiedEvent)
class ObjectModifiedEvent(object): # pragma: no cover
    def __init__(self, object):
        self.object = object
