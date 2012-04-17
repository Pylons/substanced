import inspect

from zope.interface.interfaces import IInterface
from zope.interface import (
    providedBy,
    alsoProvides,
    Interface,
    implementer,
    )
from zope.interface.interface import InterfaceClass

import venusian

from pyramid.exceptions import ConfigurationError

from ..interfaces import IContent
from ..util import dotted_name

_marker = object()

Type = Interface # API

def addbase(iface1, iface2):
    if not iface2 in iface1.__iro__:
        iface1.__bases__ += (iface2,)
        return True
    return False

class ContentRegistry(object):
    def __init__(self, category_iface=IContent):
        self.category_iface = category_iface
        self.factories = {}

    def add(self, content_iface, factory, **meta):
        addbase(content_iface, self.category_iface)
        self.factories[content_iface] = factory
        if 'name' in meta:
            name = meta.pop('name')
            self.factories[name] = factory
        for k, v in meta.items():
            content_iface.setTaggedValue(k, v)

    def create(self, content_type, *arg, **kw):
        return self.factories[content_type](*arg, **kw)

    def all(self, context=_marker, **meta):
        if context is _marker:
            candidates = [i for i in self.factories.keys()
                            if IInterface.providedBy(i)]
        else:
            candidates = [i for i in providedBy(context) if i in self.factories
                            and IInterface.providedBy(i)]
        if not meta:
            return candidates
        matches_meta = []
        for candidate in candidates:
            ok = True
            for k, v in meta.items():
                if not candidate.queryTaggedValue(k) == v:
                    ok = False
                    break
            if ok:
                matches_meta.append(candidate)
        return matches_meta

    def first(self, context, **meta):
        matching = self.all(context, **meta)
        if not matching:
            raise ValueError('No match!')
        return matching[0]

    def metadata(self, context, name, default=None):
        content_ifaces = self.all(context)
        for iface in content_ifaces:
            maybe = iface.queryTaggedValue(name, default)
            if maybe is not None:
                return maybe
        return default

# venusian decorator that marks a class as a content class
class content(object):
    """ Use as a decorator for a content factory (usually a class).  Accepts
    a content interface and a set of meta keywords."""
    venusian = venusian
    def __init__(self, content_type, **meta):
        self.content_type = content_type
        self.meta = meta

    def __call__(self, wrapped):
        if IInterface.providedBy(self.content_type):
            implementer(self.content_type)(wrapped)
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
    ``content_iface`` is an interface representing the content type.
    ``factory`` is a class or function which produces a content instance.
    ``**meta`` is an arbitrary set of keywords associated with the content
    type in the content registry.
    """
    if IInterface.providedBy(content_type):
        content_iface = content_type
    elif isinstance(content_type, basestring):
        meta['name'] = content_type
        content_iface = InterfaceClass(content_type, ())
    else:
        raise ConfigurationError(
            'The provided "content_type" argument (%r) is not a '
            'string or an interface (it does not inherit from '
            'zope.interface.Interface)' % content_type
            )

    if not content_iface.implementedBy(factory):
        # was not called by decorator
        implementer(content_iface)(factory)

    if not inspect.isclass(factory):
        factory = provides_factory(factory, content_iface)
    
    def register_factory():
        config.registry.content.add(content_iface, factory, **meta)

    if 'IFolder' in repr(content_iface):
        import pdb; pdb.set_trace()
    discrim = ('sd-content-type', content_iface)
    
    intr = config.introspectable(
        'substance d content types',
        discrim, dotted_name(content_iface),
        'substance d content type',
        )
    intr['meta'] = meta
    intr['content_iface'] = content_iface
    intr['factory'] = factory
    config.action(discrim, callable=register_factory, introspectables=(intr,))

def provides_factory(factory, content_iface):
    """ Wrap a function factory in something that applies the provides
    interface to the created object as necessary"""
    def add_provides(*arg, **kw):
        inst = factory(*arg, **kw)
        if not content_iface.providedBy(inst):
            alsoProvides(inst, content_iface)
        return inst
    for attr in ('__doc__', '__name__', '__module__'):
        if hasattr(factory, attr):
            setattr(add_provides, attr, getattr(factory, attr))
    add_provides.__orig__ = factory
    return add_provides

def includeme(config): # pragma: no cover
    config.registry.content = ContentRegistry()
    config.add_directive('add_content_type', add_content_type)

# usage:
# registry.content.create(IFoo, 'a', bar=2)
# registry.content.all(context)
# registry.content.all()
# registry.content.first(context)
# registry.content.metadata(**match)
