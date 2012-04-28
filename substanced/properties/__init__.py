from pyramid.httpexceptions import HTTPFound

from ..interfaces import IPropertied
from ..form import FormView
from ..sdi import mgmt_view
from ..event import ObjectModified

@mgmt_view(
    context=IPropertied,
    name='properties',
    renderer='templates/propertysheets.pt',
    tab_title='Properties',
    permission='sdi.edit-properties'
    )
class PropertySheetsView(FormView):
    buttons = ('save',)
    
    def __init__(self, request):
        self.request = request
        self.context = request.context
        subpath = request.subpath
        factory = None
        if subpath:
            active_sheet_name = subpath[0]
            factory = dict(self.context.__propsheets__).get(active_sheet_name)
        if not factory:
            active_sheet_name, factory = self.context.__propsheets__[0]
        self.active_sheet_name = active_sheet_name
        self.active_sheet = factory(self.context, self.request)
        self.schema = self.active_sheet.get_schema()
        self.sheet_names = [ x[0] for x in self.context.__propsheets__ ]

    def save_success(self, appstruct):
        self.active_sheet.set(appstruct)
        self.active_sheet.after_set()
        return HTTPFound(self.request.mgmt_path(
            self.context, '@@properties', self.active_sheet_name))

    def show(self, form):
        appstruct = self.active_sheet.get()
        return {'form':form.render(appstruct=appstruct)}

class PropertySheet(object):
    """ Convenience base class for concrete property sheet implementations """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get_schema(self):
        return self.schema.bind(request=self.request)

    def get(self):
        context = self.context
        return dict(context.__dict__)

    def set(self, struct):
        for k in struct:
            setattr(self.context, k, struct[k])

    def after_set(self):
        event = ObjectModified(self.context)
        self.request.registry.subscribers((self.context, event), None)
        self.request.flash_undo('Updated properties', 'success')

def includeme(config): # pragma: no cover
    config.scan('.')
    
