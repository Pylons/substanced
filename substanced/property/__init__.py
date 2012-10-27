from zope.interface import implementer
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

