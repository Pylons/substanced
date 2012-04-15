from zope.interface.interfaces import IInterface
from zope.interface import (
    providedBy,
    Interface,
    implementer,
    )

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
        for k, v in meta.items():
            content_iface.setTaggedValue(k, v)
        
    def create(self, content_iface, *arg, **kw):
        return self.factories[content_iface](*arg, **kw)

    def all(self, context=_marker, **meta):
        if context is _marker:
            candidates = self.factories.keys()
        else:
            candidates = [i for i in providedBy(context) if i in self.factories]
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
    def __init__(self, content_iface, **meta):
        self.content_iface = content_iface
        self.meta = meta

    def __call__(self, wrapped):
        implementer(self.content_iface)(wrapped)
        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            config.add_content_type(self.content_iface, wrapped, **self.meta)
        info = self.venusian.attach(wrapped, callback, category='substanced')
        self.meta['_info'] = info.codeinfo # fbo "action_method"
        return wrapped
    
def add_content_type(config, content_iface, factory, **meta):
    """
    Configurator method which adds a content type.  Call via
    ``config.add_content_type`` during Pyramid configuration phase.
    ``content_iface`` is an interface representing the content type.
    ``factory`` is a class or function which produces a content instance.
    ``**meta`` is an arbitrary set of keywords associated with the content
    type in the content registry.
    """
    if not IInterface.providedBy(content_iface):
        raise ConfigurationError(
            'The provided "content_iface" argument (%r) is not an '
            'interface object (it does not inherit from '
            'zope.interface.Interface)' % type)

    if not content_iface.implementedBy(factory):
        # was not called by decorator
        implementer(content_iface)(factory)
    
    def register_factory():
        config.registry.content.add(content_iface, factory, **meta)

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
    

def includeme(config): # pragma: no cover
    config.registry.content = ContentRegistry()
    config.add_directive('add_content_type', add_content_type)

# usage:
# registry.content.create(IFoo, 'a', bar=2)
# registry.content.all(context)
# registry.content.all()
# registry.content.first(context)
# registry.content.metadata(**match)
