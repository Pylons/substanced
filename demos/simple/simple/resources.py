import colander
import deform.widget

from persistent import Persistent

from substanced.schema import Schema
from substanced.content import content
from substanced.property import PropertySheet

@colander.deferred
def name_validator(node, kw):
    request = kw['request']
    context = request.context
    def exists(node, value):
        if request.registry.content.istype(context, 'Document'):
            if value != context.__name__:
                try:
                    context.__parent__.check_name(value)
                except Exception as e:
                    raise colander.Invalid(node, e.args[0], value)
        else:
            try:
                context.check_name(value)
            except Exception as e:
                raise colander.Invalid(node, e.args[0], value)

    return exists

class DocumentSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator = name_validator,
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

    def texts(self): # for indexing
        return self.title, self.body
        
