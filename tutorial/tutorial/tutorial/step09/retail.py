from pyramid.url import resource_url
from pyramid.view import view_config

from substanced.interfaces import (
    ISite
    )

from .interfaces import (
    IDocument,
    ITopic
)
from .layout import Layout

class SplashView(Layout):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def documents(self):
        search_catalog = self.request.search_catalog
        count, docids, resolver = search_catalog(interfaces=(IDocument,))
        return [resolver(docid) for docid in docids]

    @property
    def topics(self):
        search_catalog = self.request.search_catalog
        count, docids, resolver = search_catalog(interfaces=(ITopic,))
        return [resolver(docid) for docid in docids]

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
        for document in self.documents:
            documents.append(
                    {'url': resource_url(document,
                                         self.request),
                     'title': document.title,
                     })

        return dict(documents=documents)

    @view_config(renderer='templates/document_view.pt',
                 context=IDocument)
    def document_view(self):
        self.title = self.context.title

        objectid = -1099536351
        from substanced.service import find_service
        objectmap = find_service(self.context, 'objectmap')
        rel = 'document-to-topic'
        topic = objectmap.object_for(objectid)
        print list(objectmap.sources(topic, rel))
        print list(objectmap.targets(self.context, rel))
        #objectmap.connect(self.context, topic, 'document-to-topic')





        return dict(body=self.context.body, topic=topic)

    @view_config(renderer='templates/topics_list.pt',
                 name='topics')
    def topics_list(self):
        self.title = 'My Topics'

        topics = []
        for topic in self.topics:
            topics.append(
                    {'url': resource_url(topic,
                                         self.request),
                     'title': topic.title,
                     })

        return dict(topics=topics)

    @view_config(renderer='templates/topic_view.pt',
                 context=ITopic)
    def topic_view(self):
        self.title = self.context.title

        documents = self.documents

        # TODO this is just temporary until I wire up widget
        from substanced.util import oid_of
        oid = oid_of(self.context)

        return dict(oid=oid, documents=documents)

