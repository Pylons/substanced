from functools import update_wrapper

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
    IContentCreated,
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
    def __init__(self, object, parent, name, duplicating=False):
        self.object = object
        self.parent = parent
        self.name = name
        self.duplicating = duplicating

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

@implementer(IContentCreated)
class ContentCreated(object):
    def __init__(self, object, content_type, meta):
        self.object = object
        self.content_type = content_type
        self.meta = meta

# subscriber decorators, e.g.
# @subscribe_added(MyContent)
# def foo(event):
#     ....

class _Subscriber(object):
    venusian = venusian # for testing
    def __call__(self, wrapped):
        self.venusian.attach(wrapped, self.register, category='substanced')
        return wrapped

class _FolderEventSubscriber(_Subscriber):
    def __init__(self, obj=None, container=None, **predicates):
        if obj is None:
            obj = Interface
        if container is None:
            container = Interface
        self.obj = obj
        self.container = container
        self.predicates = predicates

    def register(self, scanner, name, wrapped):
        add_content_subscriber = getattr(
            scanner.config, 'add_content_subscriber', None)
        if add_content_subscriber is not None:
            add_content_subscriber(
                wrapped,
                [self.event, self.obj, self.container],
                **self.predicates
                )

# content events have no container associated

class _ContentEventSubscriber(_Subscriber):
    def __init__(self, obj=None, **predicates):
        if obj is None:
            obj = Interface
        self.obj = obj
        self.predicates = predicates

    def register(self, scanner, name, wrapped):
        add_content_subscriber = getattr(
            scanner.config, 'add_content_subscriber', None)
        if add_content_subscriber is not None:
            add_content_subscriber(
                wrapped,
                [self.event, self.obj],
                **self.predicates
                )

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

class subscribe_modified(_ContentEventSubscriber):
    """ Decorator for registering an object modified event subscriber
    (a subscriber for ObjectModified)."""
    event = IObjectModified

class subscribe_created(_ContentEventSubscriber):
    """ Decorator for registering an object will-be-removed event subscriber
    (a subscriber for ContentCreated)."""
    event = IContentCreated
    
def add_content_subscriber(config, subscriber, iface=None, **predicates):
    """ Configurator directive that works like Pyramid's ``add_subscriber``,
    except it wraps the subscriber in something that first adds the
    ``registry`` attribute to the event being sent before the wrapped
    subscriber is called."""
    registry = config.registry
    def wrapper(event, *arg): # *arg ignored
        event.registry = registry
        return subscriber(event)
    if hasattr(subscriber, '__name__'):
        update_wrapper(wrapper, subscriber)
    wrapper.wrapped = subscriber
    config.add_subscriber(wrapper, iface, **predicates)

class _ContentTypePredicate(object):
    def __init__(self, val, config):
        self.val = val
        self.registry = config.registry

    def phash(self):
        return 'content_type = %s' % (self.val,)

    text = phash

    def __call__(self, event, *arg):
        # NB: accept *arg so we can be used as either a folder event
        # predicate or as a content event predicate.  (yes, it's lame).
        return self.registry.content.istype(event.object, self.val)
    
def include(config): # pragma: no cover
    config.add_directive('add_content_subscriber', add_content_subscriber)
    config.add_subscriber_predicate('content_type', _ContentTypePredicate)

includeme = include

