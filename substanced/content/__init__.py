from zope.interface.interfaces import IInterface
from zope.interface import (
    providedBy,
    Interface,
    implementer,
    )

import venusian

from pyramid.exceptions import ConfigurationError

from ..interfaces import IContent

_marker = object()

Type = Interface # API

def addbase(iface1, iface2):
    if not iface2 in iface1.__iro__:
        iface1.__bases__ += (iface2,)
        return True
    return False

class ContentCategory(object):
    def __init__(self, category_iface):
        self.category_iface = category_iface
        self.factories = {}

    def add(self, content_iface, factory, **meta):
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

class ContentCategories(object):
    def __init__(self):
        self.categories = {}

    def add(self, content_iface, factory, **meta):
        category_iface = meta.get('category')
        if category_iface is None:
            category_iface = IContent
        if category_iface is not None:
            addbase(content_iface, category_iface)
        category = self.categories.setdefault(category_iface,
                                              ContentCategory(category_iface))
        category.add(content_iface, factory, **meta)

    def __getitem__(self, category_iface):
        return self.categories[category_iface]

    def create(self, content_iface, *arg, **kw):
        return self.categories[IContent].create(content_iface, *arg, **kw)

    def all(self, context=_marker, **meta):
        return self.categories[IContent].all(context, **meta)

    def first(self, context, **meta):
        return self.categories[IContent].first(context, **meta)

    def metadata(self, context, name, default=None):
        return self.categories[IContent].metadata(context, name, default)
    
# venusian decorator that marks a class as a content class
class content(object):
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
    if not IInterface.providedBy(content_iface):
        raise ConfigurationError(
            'The provided "content_iface" argument (%r) is not an '
            'interface object (it does not inherit from '
            'zope.interface.Interface' % type)

    category_iface = meta.get('category')

    if category_iface is not None:

        if not IInterface.providedBy(category_iface):
            raise ConfigurationError(
                'The provided "category" argument (%r) is not an '
                'interface object (it does not inherit from '
                'zope.interface.Interface' % type)

    if not content_iface.implementedBy(factory):
        # was not called by decorator
        implementer(content_iface)(factory)
    
    def register_factory():
        config.registry.content.add(content_iface, factory, **meta)

    discrim = ('content-type', content_iface, category_iface)
    config.action(discrim, callable=register_factory)
    

def includeme(config): # pragma: no cover
    config.registry.content = ContentCategories()
    config.add_directive('add_content_type', add_content_type)

# usage:
# registry.content[IContent].create(IFoo, 'a', bar=1)
# registry.content.create(IFoo, a', bar=2)
# registry.content.[IContent].all(context)
# registry.content.all(context)
# registry.content.[IContent].all()
# registry.content.all()
# registry.content[IContent].first(context)
# registry.content.first(context)

