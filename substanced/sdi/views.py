from pyramid_deform import FormView
from pyramid.renderers import get_renderer
from pyramid.httpexceptions import HTTPFound

class ContentView(FormView):

    buttons = ('save',)
    
    def __init__(self, request):
        template = get_renderer('templates/master.pt').implementation()
        self.macros = {'master':template}
        self.request = request
        self.context = request.context
        self.schema = self.context.__schema__

    def save_success(self, appstruct):
        self.context.__dict__.update(appstruct)
        self.context._p_changed = True
        self.request.session.flash('Updated')
        return HTTPFound('/manage' + self.request.resource_path(self.context))

    def show(self, form):
        appstruct = self.context.__dict__
        return {'form':form.render(appstruct=appstruct)}
        
