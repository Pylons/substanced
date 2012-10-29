import colander
import deform.widget

from persistent import Persistent

from substanced.content import content
from substanced.property import PropertySheet
from substanced.schema import (
    Schema,
    NameSchemaNode
    )

def context_is_a_document(context, request):
    return request.registry.content.istype(context, 'Document')

class DocumentSchema(Schema):
    name = NameSchemaNode(
        editing=context_is_a_document,
        )
    title = colander.SchemaNode(
        colander.String(),
        )
    body = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.RichTextWidget()
        )

class DocumentPropertySheet(PropertySheet):
    schema = DocumentSchema()
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        context = self.context
        return dict(
            name=context.__name__,
            body=context.body,
            title=context.title
            )

    def set(self, struct):
        context = self.context
        newname = struct['name']
        oldname = context.__name__
        if newname != oldname:
            parent = context.__parent__
            parent.rename(oldname, newname)
        context.body = struct['body']
        context.title = struct['title']

@content(
    'Document',
    icon='icon-align-left',
    add_view='add_document', 
    propertysheets = (
        ('Basic', DocumentPropertySheet),
        ),
    catalog=True,
    )
class Document(Persistent):
    def __init__(self, title, body):
        self.title = title
        self.body = body

        
