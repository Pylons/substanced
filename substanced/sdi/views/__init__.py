from pyramid.httpexceptions import HTTPFound

from ...interfaces import IPropertied

from .. import mgmt_view
from ...form import FormView

@mgmt_view(context=IPropertied, name='properties', renderer='templates/form.pt',
           tab_title='Properties', permission='edit properties')
class PropertiesView(FormView):

    buttons = ('save',)
    
    def __init__(self, request):
        self.request = request
        self.context = request.context
        self.schema = self.context.__propschema__

    def save_success(self, appstruct):
        self.context.set_properties(appstruct)
        self.request.session.flash('Updated')
        return HTTPFound(self.request.mgmt_path(self.context, '@@properties'))

    def show(self, form):
        appstruct = self.context.get_properties()
        return {'form':form.render(appstruct=appstruct)}

