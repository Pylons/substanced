import inspect

from pyramid.exceptions import ConfigurationError

from zope.interface.interfaces import IInterface

from zope.interface import (
    alsoProvides,
    Interface,
    implementer,
    implementedBy,
    )

import venusian

from ..interfaces import (
    IContent,
    ICatalogable,
    IPropertied,
    )

_marker = object()

def get_content_type(context):
    return getattr(context, '__content_type__', None)

def set_content_type(context, content_type):
    has_type = context.__dict__.get('__content_type__')
    if has_type is not None:
        raise ConfigurationError(
            'The context %s already has a content type (%s)' % (
                context, has_type))
    context.__content_type__ = content_type

class ContentRegistry(object):
    def __init__(self):
        self.factories = {}
        self.meta = {}

    def add(self, content_type, factory, **meta):
        self.factories[content_type] = factory
        self.meta[content_type] = meta

    def all(self):
        return list(self.factories.keys())

    def create(self, content_type, *arg, **kw):
        return self.factories[content_type](*arg, **kw)

    def metadata(self, context, name, default=None):
        content_type = self.typeof(context)
        maybe = self.meta.get(content_type, {}).get(name)
        if maybe is not None:
            return maybe
        return default

    def typeof(self, context):
        return get_content_type(context)

    def istype(self, context, content_type):
        return content_type == get_content_type(context)

    def exists(self, content_type):
        return content_type in self.factories.keys()

def _get_meta_interfaces(content_type, factory, meta):
    interfaces = set(implementedBy(factory))
    interfaces.add(IContent)

    extra_interfaces = set(meta.get('interfaces', []))
    interfaces.update(extra_interfaces)

    if IInterface.providedBy(content_type):
        interfaces.add(content_type)

    if meta.get('catalog'):
        interfaces.add(ICatalogable)

    if meta.get('propertysheets') is not None:
        interfaces.add(IPropertied)

    interfaces.discard(Interface)

    return interfaces
    
# venusian decorator that marks a class as a content class
class content(object):
    """ Use as a decorator for a content factory (usually a class).  Accepts
    a content interface and a set of meta keywords."""
    venusian = venusian
    def __init__(self, content_type, **meta):
        self.content_type = content_type
        self.meta = meta

    def __call__(self, wrapped):
        interfaces = _get_meta_interfaces(self.content_type, wrapped, self.meta)
        implementer(*interfaces)(wrapped)
        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            config.add_content_type(self.content_type, wrapped, **self.meta)
        info = self.venusian.attach(wrapped, callback, category='substanced')
        self.meta['_info'] = info.codeinfo # fbo "action_method"
        return wrapped

def add_content_type(config, content_type, factory, **meta):
    """
    Configurator method which adds a content type.  Call via
    ``config.add_content_type`` during Pyramid configuration phase.
    ``content_type`` is a hashable object (usually a string) representing the
    content type.  ``factory`` is a class or function which produces a
    content instance.  ``**meta`` is an arbitrary set of keywords associated
    with the content type in the content registry.

    Some of the keywords in ``**meta`` have special meaning:

    - If ``meta`` contains the keyword ``propertysheets``, the content type
      will obtain a tab in the SDI that allows users to manage its
      properties.

    - If ``meta`` contains the keyword ``catalog`` and its value is true, the
      object will be tracked in the Substance D catalog.

    - If ``meta`` contains the keyword ``interfaces``, its value must be a
      sequence of :term:`interface` objects.  These interfaces will be
      applied to the content object (or if the factory is a class, to its
      class).

    Other keywords will just be stored, and have no special meaning.
    """
    # NB: it's intentional that if this function is called by the ``content``
    # decorator that we reset the implemented interfaces; it's idempotent and
    # this is for benefit of someone who is not using the decorator.
    interfaces = _get_meta_interfaces(content_type, factory, meta)
    implementer(*interfaces)(factory)

    set_content_type(factory, content_type)

    if not inspect.isclass(factory):
        factory = provides_factory(factory, content_type, interfaces)

    def register_factory():
        config.registry.content.add(content_type, factory, **meta)

    discrim = ('sd-content-type', content_type)
    
    intr = config.introspectable(
        'substance d content types',
        discrim,
        content_type,
        'substance d content type',
        )
    intr['meta'] = meta
    intr['content_type'] = content_type
    intr['interfaces'] = interfaces
    intr['factory'] = factory
    config.action(discrim, callable=register_factory, introspectables=(intr,))

def provides_factory(factory, content_type, interfaces):
    """ Wrap a function factory in something that applies the provides
    interfaces to the created object as necessary"""
    def add_provides(*arg, **kw):
        inst = factory(*arg, **kw)
        alsoProvides(inst, *interfaces)
        set_content_type(inst, content_type)
        return inst
    for attr in ('__doc__', '__name__', '__module__'):
        if hasattr(factory, attr):
            setattr(add_provides, attr, getattr(factory, attr))
    add_provides.__orig__ = factory
    return add_provides

def includeme(config): # pragma: no cover
    config.registry.content = ContentRegistry()
    config.add_directive('add_content_type', add_content_type)

