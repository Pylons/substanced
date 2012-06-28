from zope.interface import implementer

from .interfaces import (
    IObjectAdded,
    IObjectWillBeAdded,
    IObjectRemoved,
    IObjectWillBeRemoved,
    IObjectModified,
    )
    
class _ObjectEvent(object):
    def __init__(self, object, parent, name):
        self.object = object
        self.parent = parent
        self.name = name

@implementer(IObjectAdded)
class ObjectAdded(_ObjectEvent):
    """ An event sent just after an object has been added to a folder.  """

@implementer(IObjectWillBeAdded)
class ObjectWillBeAdded(_ObjectEvent):
    """ An event sent just before an object has been added to a folder.  """
    def __init__(self, object, parent, name, is_duplicated):
        self.object = object
        self.parent = parent
        self.name = name
        self.is_duplicated = is_duplicated

class _ObjectRemovalEvent(object):
    def __init__(self, object, parent, name, moving=False):
        self.object = object
        self.parent = parent
        self.name = name
        self.moving = moving

@implementer(IObjectRemoved)
class ObjectRemoved(_ObjectRemovalEvent):
    """ An event sent just after an object has been removed from a folder."""

@implementer(IObjectWillBeRemoved)
class ObjectWillBeRemoved(_ObjectRemovalEvent):
    """ An event sent just before an object has been removed from a folder."""

@implementer(IObjectModified)
class ObjectModified(object): # pragma: no cover
    """ An event sent when an object has been modified."""
    def __init__(self, object):
        self.object = object
