from pyramid.httpexceptions import HTTPFound

from ..interfaces import IPropertied
from ..form import FormView
from ..sdi import mgmt_view
from ..event import ObjectModified

@mgmt_view(context=IPropertied, name='properties',
           renderer='substanced:sdi/templates/form.pt',
           tab_title='Properties', permission='sdi.edit-properties')
class PropertiesView(FormView):

    buttons = ('save',)
    
    def __init__(self, request):
        self.request = request
        self.context = request.context
        self.schema = self.context.__propschema__

    def save_success(self, appstruct):
        self.context.set_properties(appstruct)
        event = ObjectModified(self.context)
        self.request.registry.subscribers((self.context, event), None)
        self.request.flash_undo('Updated properties', 'success')
        return HTTPFound(self.request.mgmt_path(self.context, '@@properties'))

    def show(self, form):
        appstruct = self.context.get_properties()
        return {'form':form.render(appstruct=appstruct)}

def includeme(config): # pragma: no cover
    config.scan('.')
    
