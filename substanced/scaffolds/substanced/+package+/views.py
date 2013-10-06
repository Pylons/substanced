from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import get_renderer
from pyramid.view import view_config

from substanced.sdi import mgmt_view
from substanced.form import FormView
from substanced.interfaces import IFolder

from .resources import Document
from .resources import DocumentSchema

#
#   SDI "add" view for documents
#
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
        name = appstruct.pop('name')
        document = registry.content.create('Document', **appstruct)
        self.context[name] = document
        return HTTPFound(
            self.request.sdiapi.mgmt_path(self.context, '@@contents')
            )
