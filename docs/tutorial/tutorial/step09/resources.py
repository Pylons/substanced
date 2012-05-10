import colander
import deform.widget
from deform_bootstrap.widget import ChosenSingleWidget

from persistent import Persistent

from substanced.schema import Schema
from substanced.content import content
from substanced.property import PropertySheet
from substanced.service import find_service
from substanced.util import oid_of

from .interfaces import (
    IDocument,
    ITopic
    )

DocumentToTopic = 'document-to-topic'

@colander.deferred
def pepper_widget(node, kw):
    context = kw['context']
    request = kw['request']
    search_catalog = request.search_catalog
    count, oids, resolver = search_catalog(interfaces=(ITopic,))
    values = []
    for oid in oids:
        title = resolver(oid).title
        values.append(
            (oid, title)
        )
    return ChosenSingleWidget(values=values)


class DocumentSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
    )
    title = colander.SchemaNode(
        colander.String(),
    )
    body = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.RichTextWidget()
    )
    topic = colander.SchemaNode(
        colander.Int(),
        widget=pepper_widget,
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
        newname = struct['name']
        oldname = context.__name__
        if newname != oldname:
            parent = context.__parent__
            parent.rename(oldname, newname)
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

    def _resolve_topic(self, topic_or_topicid):
        objectmap = find_service(self, 'objectmap')
        if oid_of(topic_or_topicid, None) is None:
            # it's a topic id
            topic = objectmap.object_for(topic_or_topicid)
        else:
            topic = topic_or_topicid
        return topic

    def get_topicids(self):
        objectmap = find_service(self, 'objectmap')
        return objectmap.targetids(self, DocumentToTopic)

    def connect(self, *topics):
        """ Connect this document to one or more topic objects or
        topic objectids."""
        objectmap = find_service(self, 'objectmap')
        for topicid in topics:
            topic = self._resolve_topic(topicid)
            if topic is not None:
                objectmap.connect(self, topic, DocumentToTopic)

    def disconnect(self, *topics):
        """ Disconnect this category from one or more topic objects or
        topic objectids."""
        if not topics:
            topics = self.get_topicids()
        objectmap = find_service(self, 'objectmap')
        for topicid in topics:
            topic = self._resolve_topic(topicid)
            if topic is not None:
                objectmap.disconnect(self, topic, DocumentToTopic)


# Topics
class TopicSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
    )
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
        newname = struct['name']
        oldname = context.__name__
        if newname != oldname:
            parent = context.__parent__
            parent.rename(oldname, newname)
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

