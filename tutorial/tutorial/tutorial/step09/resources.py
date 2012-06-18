import colander
import deform.widget
from deform_bootstrap.widget import ChosenSingleWidget

from persistent import Persistent

from substanced.schema import Schema
from substanced.content import content
from substanced.property import PropertySheet
from substanced.service import find_service

from .interfaces import (
    IDocument,
    ITopic
    )

DocumentToTopic = 'document-to-topic'

@colander.deferred
def topics_widget(node, kw):
    request = kw['request']
    search_catalog = request.search_catalog
    count, oids, resolver = search_catalog(interfaces=(ITopic,))
    values = []
    for oid in oids:
        title = resolver(oid).title
        values.append(
            (str(oid), title)
        )
    return ChosenSingleWidget(values=values)


class DocumentSchema(Schema):
    title = colander.SchemaNode(
        colander.String(),
    )
    body = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.RichTextWidget()
    )
    topic = colander.SchemaNode(
        colander.Int(),
        widget=topics_widget,
        missing=colander.null
    )


class DocumentBasicPropertySheet(PropertySheet):
    schema = DocumentSchema()

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        context = self.context

        # Need the objectid of the first referenced topic
        topics = list(context.get_topicids())
        if not topics:
            topic = colander.null
        else:
            topic = topics[0]

        return dict(
            name=context.__name__,
            title=context.title,
            body=context.body,
            topic=topic
        )

    def set(self, struct):
        context = self.context
        context.title = struct['title']
        context.body = struct['body']

        # Disconnect old relations, make new relations
        context.disconnect()
        context.connect(struct['topic'])


@content(
    IDocument,
    name='Document',
    icon='icon-align-left',
    add_view='add_document',
    propertysheets=(
        ('Basic', DocumentBasicPropertySheet),
        ),
    catalog=True,
    )
class Document(Persistent):
    def __init__(self, title, body, topic):
        self.title = title
        self.body = body
        self.topic = topic

    def texts(self): # for indexing
        return self.title, self.body

    def get_topicids(self):
        objectmap = find_service(self, 'objectmap')
        return objectmap.targetids(self, DocumentToTopic)

    def connect(self, *topics):
        objectmap = find_service(self, 'objectmap')
        for topicid in topics:
            objectmap.connect(self, topicid, DocumentToTopic)

    def disconnect(self):
        topics = self.get_topicids()
        objectmap = find_service(self, 'objectmap')
        for topicid in topics:
            objectmap.disconnect(self, topicid, DocumentToTopic)


# Topics
class TopicSchema(Schema):
    title = colander.SchemaNode(
        colander.String(),
    )


class TopicBasicPropertySheet(PropertySheet):
    schema = TopicSchema()

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        context = self.context
        return dict(
            name=context.__name__,
            title=context.title
        )

    def set(self, struct):
        context = self.context
        context.title = struct['title']


@content(
    ITopic,
    name='Topic',
    icon='icon-align-left',
    add_view='add_topic',
    propertysheets=(
        ('Basic', TopicBasicPropertySheet),
        ),
    catalog=True,
    )

class Topic(Persistent):
    def __init__(self, title):
        self.title = title

    def texts(self): # for indexing
        return self.title

    @property
    def document(self):
        #objectmap = find_service(self, 'objectmap')
        #return objectmap.sources(self, 'document-to-topic')
        return None

