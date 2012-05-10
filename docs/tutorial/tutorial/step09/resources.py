import colander
import deform.widget

from persistent import Persistent

from substanced.schema import Schema
from substanced.content import content
from substanced.property import PropertySheet
from substanced.service import find_service

from .interfaces import (
    IDocument,
    ITopic
    )

import deform_bootstrap.widget
from substanced.util import oid_of
@colander.deferred
def principals_widget(node, kw):
    request = kw['request']
    principals = find_service(request.context, 'principals')
    groups = [(str(oid_of(group)), name) for name, group in
                                         principals['groups'].items()]
    users = [(str(oid_of(user)), name) for name, user in
                                       principals['users'].items()]
    values = (
            {'label':'Groups', 'values':groups},
            {'label':'Users', 'values':users},
        )
    widget = deform_bootstrap.widget.ChosenOptGroupWidget(values=values)
    return widget

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
    principal = colander.SchemaNode(
        colander.Int(),
        missing=colander.null,
        widget = principals_widget,
        )


class DocumentBasicPropertySheet(PropertySheet):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        context = self.context
        topic = context.topic
        return dict(
            name=context.__name__,
            title=context.title,
            body=context.body,
            topic=context.topic
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

        # Make the relationship to a topic
        #objectmap = find_service(context, 'objectmap')
        #objectid = struct['topic']
        #topic = objectmap.object_for(objectid)
        #objectmap.connect(context, topic, 'document-to-topic')


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
    def __init__(self, title, body):
        self.title = title
        self.body = body

    def texts(self): # for indexing
        return self.title, self.body


    @property
    def topic(self):
        #objectmap = find_service(self, 'objectmap')
        #topics = list(objectmap.targets(self, 'document-to-topic'))
        #topic = 0
        #for t in topics:
        #    topic = t
        #return topic

        return None

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

