import colander
import deform.widget

from persistent import Persistent

from substanced.schema import Schema
from substanced.content import content
from substanced.property import PropertySheet

from .interfaces import (
    IDocument,
    ITopic
)

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

class DocumentBasicPropertySheet(PropertySheet):
    schema = DocumentSchema()

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        context = self.context
        return dict(
            name=context.__name__,
            title=context.title,
            body=context.body
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

@content(
    IDocument,
    name='Document',
    icon='icon-align-left',
    add_view='add_document',
    propertysheets = (
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
    propertysheets = (
        ('Basic', TopicBasicPropertySheet),
        ),
    catalog=True,
    )
class Topic(Persistent):
    def __init__(self, title):
        self.title = title

    def texts(self): # for indexing
        return self.title

