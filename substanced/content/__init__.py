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

    def add(self, content_iface, factory):
        self.factories[content_iface] = factory
        
    def create(self, content_iface, *arg, **kw):
        return self.factories[content_iface](*arg, **kw)

    def provided_by(self, resource):
        return self.category_iface.providedBy(resource)

    def all(self, context=_marker):
        if context is _marker:
            return self.factories.keys()
        return [i for i in providedBy(context) if i in self.factories]

    def first(self, context):
        ifaces = [i for i in providedBy(context) if i in self.factories]
        if not ifaces:
            raise ValueError('%s is not content' % context)
        return ifaces[0]

    def get_meta(self, context, name, default=None):
        try:
            content_iface = self.first(context)
        except ValueError:
            return None
        return content_iface.queryTaggedValue(name, default)

class ContentCategories(object):
    def __init__(self):
        self.categories = {}

    def add(self, content_iface, factory, category_iface=None):
        if category_iface is None:
            category_iface = IContent
        addbase(content_iface, category_iface)
        implementer(content_iface)(factory)
        category = self.categories.setdefault(category_iface,
                                              ContentCategory(category_iface))
        category.add(content_iface, factory)

    def __getitem__(self, category_iface):
        return self.categories[category_iface]

    def create(self, content_iface, *arg, **kw):
        return self.categories[IContent].create(content_iface, *arg, **kw)

    def provided_by(self, resource):
        return self.categories[IContent].provided_by(resource)

    def all(self, context):
        return self.categories[IContent].all(context)

    def get_meta(self, context, name, default=None):
        return self.categories[IContent].get_meta(context, name, default)
    
# venusian decorator that marks a class as a content class
class content(object):
    venusian = venusian
    def __init__(self, content_iface, category_iface=None):
        self.content_iface = content_iface
        self.category_iface = category_iface

    def __call__(self, wrapped):
        settings = dict(category_iface=self.category_iface)
        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            config.add_content_type(self.content_iface, wrapped, **settings)
        info = self.venusian.attach(wrapped, callback, category='substanced')
        settings['_info'] = info.codeinfo # fbo "action_method"
        return wrapped
    
def add_content_type(config, content_iface, factory, category_iface=None):
    if not IInterface.providedBy(content_iface):
        raise ConfigurationError(
            'The provided "content_iface" argument (%r) is not an '
            'interface object (it does not inherit from '
            'zope.interface.Interface' % type)

    if category_iface is not None:

        if not IInterface.providedBy(category_iface):
            raise ConfigurationError(
                'The provided "category_iface" argument (%r) is not an '
                'interface object (it does not inherit from '
                'zope.interface.Interface' % type)
        
    def register_factory():
        config.registry.content.add(content_iface, factory, category_iface)

    discrim = ('content-type', content_iface, category_iface)
    config.action(discrim, callable=register_factory)
    

def includeme(config): # pragma: no cover
    config.registry.content = ContentCategories()
    config.add_directive('add_content_type', add_content_type)

# usage:
# registry.content[IContent].create(IFoo, 'a', bar=1)
# registry.content.create(IFoo, a', bar=2)
# registry.content.[IContent].provided_by(model)
# registry.content.provided_by(model)
# registry.content.[IContent].all(context)
# registry.content.all(context)
# registry.content.[IContent].all()
# registry.content.all()
# registry.content[IContent].first(context)
# registry.content.first(context)

