from pyramid.httpexceptions import HTTPFound

from substanced.sdi import mgmt_view
from substanced.form import FormView
from substanced.interfaces import (
    IFolder,
    )

from .interfaces import IDocument
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
        name = appstruct.pop('name')
        document = registry.content.create(IDocument,
                                           **appstruct)
        self.context[name] = document
        return HTTPFound(self.request.mgmt_path(document, '@@properties'))

