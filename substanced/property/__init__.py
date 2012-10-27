from zope.interface import implementer

from pyramid.threadlocal import get_current_registry

from ..interfaces import IPropertySheet
from ..event import ObjectModified

@implementer(IPropertySheet)
class PropertySheet(object):
    """ Convenience base class for concrete property sheet implementations """

    # XXX probably should be decorator for set and get
    permissions = (
        ('view', 'sdi.view'),
        ('change', 'sdi.edit-properties'),
        )

    schema = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        context = self.context
        if hasattr(context, '_p_activate'):
            context._p_activate()
        return dict(context.__dict__)

    def set(self, struct):
        for k in struct:
            setattr(self.context, k, struct[k])

    def after_set(self):
        event = ObjectModified(self.context)
        self.request.registry.subscribers((self.context, event), None)
        self.request.flash_with_undo('Updated properties', 'success')

def is_propertied(resource, registry=None):
    if registry is None:
        registry = get_current_registry()
    sheets = registry.content.metadata(resource, 'propertysheets', None)
    return sheets is not None

class _PropertiedPredicate(object):
    is_propertied = staticmethod(is_propertied) # for testing
    
    def __init__(self, val, config):
        self.val = bool(val)
        self.registry = config.registry

    def text(self):
        return 'propertied = %s' % self.val

    phash = text

    def __call__(self, context, request):
        return self.is_propertied(context, self.registry) == self.val

def include(config):
    config.add_view_predicate('propertied', _PropertiedPredicate)

includeme = include
