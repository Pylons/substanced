import colander

from persistent import Persistent

from substanced.schema import Schema
from substanced.content import content
from substanced.property import PropertySheet

class DocumentSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        )
    title = colander.SchemaNode(
        colander.String(),
    )

class DocumentAdvancedSchema(Schema):
    age = colander.SchemaNode(
        colander.Integer(),
        missing="0",
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

class DocumentAdvancedPropertySheet(PropertySheet):
    schema = DocumentAdvancedSchema()

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        return dict(
            age=self.context.age
        )

    def set(self, struct):
        self.context.age = struct['age']

@content(
    'Document',
    icon='icon-align-left',
    add_view='add_document',
    propertysheets = (
        ('Basic', DocumentBasicPropertySheet),
        ('Advanced', DocumentAdvancedPropertySheet),
        )
    )
class Document(Persistent):
    def __init__(self, title, age=0):
        self.title = title
        self.age = age
