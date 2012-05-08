from pyramid.httpexceptions import HTTPFound

from substanced.sdi import mgmt_view
from substanced.form import FormView
from substanced.interfaces import (
    IFolder,
    )

from .interfaces import (
    IDocument,
    ITopic
)
from .resources import (
    DocumentSchema,
    TopicSchema
)

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
        topic = appstruct.pop('topic')
        document = registry.content.create(IDocument,
                                           **appstruct)

        self.context[name] = document
        return HTTPFound(self.request.mgmt_path(document, '@@properties'))

@mgmt_view(
    context=IFolder,
    name='add_topic',
    tab_title='Add Topic',
    permission='sdi.add-content',
    renderer='substanced.sdi:templates/form.pt',
    tab_condition=False,
    )
class AddTopicView(FormView):
    title = 'Add Topic'
    schema = TopicSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('name')
        topic = registry.content.create(ITopic,
                                           **appstruct)
        self.context[name] = topic
        return HTTPFound(self.request.mgmt_path(topic, '@@properties'))

