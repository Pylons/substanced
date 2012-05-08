from pyramid.url import resource_url
from pyramid.view import view_config

from substanced.interfaces import (
    ISite
    )

from .interfaces import IDocument
from .layout import Layout

class SplashView(Layout):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(renderer='templates/siteroot_view.pt',
                 context=ISite)
    def siteroot_view(self):
        self.title = 'Welcome to My Site'
        return {}

    @view_config(renderer='templates/documents_list.pt',
                 name='documents')
    def documents_list(self):
        self.title = 'My Documents'
        documents = []
        for name, item in self.context.items():
            if IDocument.providedBy(item):
                documents.append(
                        {'url': resource_url(item, self.request),
                         'title': item.title,
                         })
        return dict(documents=documents)

    @view_config(renderer='templates/document_view.pt',
                 context=IDocument)
    def document_view(self):
        self.title = self.context.title
        return {}

