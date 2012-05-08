from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from substanced.sdi import mgmt_view
from substanced.form import FormView
from substanced.interfaces import IFolder

from .resources import (
    DocumentSchema,
    )

from .layout import Layout

class SplashView(Layout):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        settings = request.registry.settings
        self.manage_prefix = settings.get('substanced.manage_prefix',
                                          '/manage')

    @view_config(renderer='templates/splash.pt')
    def splash_view(self):
        return {}


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
        return HTTPFound(self.request.mgmt_path(document, '@@properties'))

