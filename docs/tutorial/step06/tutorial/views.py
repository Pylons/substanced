from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from substanced.sdi import mgmt_view
from substanced.form import FormView
from substanced.interfaces import IFolder

from .resources import DocumentSchema

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


@mgmt_view(
    context=IFolder,
    name='grid_view',
    tab_title='Grid',
    permission='sdi.add-content',
    renderer='templates/grid_view.pt'
)
def grid_view(context, request):
    # Filter only the folder items that have a "title"
    json_url = request.resource_url(context, 'grid_items.json')
    return dict(json_url=json_url)


@view_config(context=IFolder, name='grid_items.json', renderer='json')
def grid_items(context, request):
    items = []
    for item in context.values():
        if getattr(item, 'title', False):
            items.append(
                dict(
                    title=item.title,
                    name=item.__name__,
                    url=request.mgmt_path(item, '@@manage_main')
                )
            )
    return items

