from pyramid_deform import FormView
from pyramid.httpexceptions import HTTPFound

from ...interfaces import IContent

from .. import mgmt_view

@mgmt_view(context=IContent, name='properties', renderer='templates/form.pt')
class PropertiesView(FormView):

    buttons = ('save',)
    
    def __init__(self, request):
        self.request = request
        self.context = request.context
        self.schema = self.context.__schema__

    def save_success(self, appstruct):
        self.context.__dict__.update(appstruct)
        self.context._p_changed = True
        self.request.session.flash('Updated')
        return HTTPFound(self.request.mgmt_path(self.context, '@@properties'))

    def show(self, form):
        appstruct = self.context.__dict__
        return {'form':form.render(appstruct=appstruct)}

