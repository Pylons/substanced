import venusian

from zope.interface import (
    implementer,
    Interface,
    )

from ..interfaces import (
    IObjectAdded,
    IObjectWillBeAdded,
    IObjectRemoved,
    IObjectWillBeRemoved,
    IObjectModified,
    IRootCreated,
    )
    
class _ObjectEvent(object):
    registry = None # added by _FolderEventSubscriber
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
    def __init__(self, object, parent, name, duplicating=False):
        self.object = object
        self.parent = parent
        self.name = name
        self.duplicating = duplicating

class _ObjectRemovalEvent(object):
    registry = None # added by _FolderEventSubscriber
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
    registry = None # added by _FolderEventSubscriber
    def __init__(self, object):
        self.object = object

@implementer(IRootCreated)
class RootCreated(object):
    def __init__(self, object, request):
        self.object = object
        self.request = request

# subscriber decorators, e.g.
# @subscribe_added(MyContent)
# def foo(event):
#     ....

class _FolderEventSubscriber(object):
    venusian = venusian # for testing

    def __init__(self, obj=None, container=None):
        if obj is None:
            obj = Interface
        if container is None:
            container = Interface
        self.obj = obj
        self.container = container

    def register(self, scanner, name, wrapped):
        registry = scanner.config.registry
        def wrapper(event, obj, container):
            event.registry = registry
            return wrapped(event)
        wrapper.wrapped = wrapped
        scanner.config.add_subscriber(wrapper,
                                      [self.event, self.obj, self.container])

    def __call__(self, wrapped):
        self.venusian.attach(wrapped, self.register, category='substanced')
        return wrapped

class subscribe_added(_FolderEventSubscriber):
    """ Decorator for registering an object added event subscriber
    (a subscriber for ObjectAdded)."""
    event = IObjectAdded

class subscribe_removed(_FolderEventSubscriber):
    """ Decorator for registering an object removed event subscriber
    (a subscriber for ObjectRemoved)."""
    event = IObjectRemoved

class subscribe_will_be_added(_FolderEventSubscriber):
    """ Decorator for registering an object will-be-added event subscriber
    (a subscriber for ObjectWillBeAdded)."""
    event = IObjectWillBeAdded

class subscribe_will_be_removed(_FolderEventSubscriber):
    """ Decorator for registering an object will-be-removed event subscriber
    (a subscriber for ObjectWillBeRemoved)."""
    event = IObjectWillBeRemoved

class subscribe_modified(_FolderEventSubscriber):
    """ Decorator for registering an object will-be-removed event subscriber
    (a subscriber for ObjectModified)."""
    event = IObjectModified
