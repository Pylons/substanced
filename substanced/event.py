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
    """ An event sent just after an object has been added to a folder.  """

@implementer(IObjectWillBeAddedEvent)
class ObjectWillBeAddedEvent(_ObjectEvent):
    """ An event sent just before an object has been added to a folder.  """

class _ObjectRemovalEvent(object):
    def __init__(self, object, parent, name, moving=False):
        self.object = object
        self.parent = parent
        self.name = name
        self.moving = moving

@implementer(IObjectRemovedEvent)
class ObjectRemovedEvent(_ObjectRemovalEvent):
    """ An event sent just after an object has been removed from a folder."""

@implementer(IObjectWillBeRemovedEvent)
class ObjectWillBeRemovedEvent(_ObjectRemovalEvent):
    """ An event sent just before an object has been removed from a folder."""

@implementer(IObjectModifiedEvent)
class ObjectModifiedEvent(object): # pragma: no cover
    """ An event sent when an object has been modified."""
    def __init__(self, object):
        self.object = object
