from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from substanced.sdi import mgmt_view
from substanced.form import FormView
from substanced.interfaces import IFolder

from .resources import DocumentSchema

@view_config(renderer='templates/hello.pt')
def splash_view(request):
    manage_prefix = request.registry.settings.get(
        'substanced.manage_prefix', '/manage')
    return {'manage_prefix': manage_prefix}


@mgmt_view(
    context=IFolder,
    name='add_document',
    tab_title='Add Document',
    permission='sdi.add-content',
    renderer='substanced.sdi:templates/form.pt',
    tab_condition=False,
    )
class AddDocumentView(FormView):
    title = 'Add Document'
    schema = DocumentSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        document = registry.content.create('Document', **appstruct)
        # Simple algorithm to construct a name from the title
        name = appstruct['title'].lower().replace(' ', '-')
        self.context[name] = document
        return HTTPFound(self.request.mgmt_path(document))

