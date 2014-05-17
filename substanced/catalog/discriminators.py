from zope.interface import providedBy

from pyramid.threadlocal import get_current_registry

from ..interfaces import IIndexView

_marker = object()

class IndexViewDiscriminator(object):
    get_current_registry = staticmethod(get_current_registry) # for testing
    
    def __init__(self, catalog_name, index_name):
        self.catalog_name = catalog_name
        self.index_name = index_name

    def __call__(self, resource, default):
        registry = self.get_current_registry() # XXX lame
        composite_name = '%s|%s' % (self.catalog_name, self.index_name)
        resource_iface = providedBy(resource)
        index_view = registry.adapters.lookup(
            (resource_iface,),
            IIndexView,
            name=composite_name,
            default=None,
            )
        if index_view is None:
            return default
        return index_view(resource, default)

class AllowedIndexDiscriminator(object):
    """ bw compat for unpickling only; safe to delete after system catalog has
    been resynced"""
    pass

def dummy_discriminator(object, default):
    return default
