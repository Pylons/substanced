import colander

from persistent import Persistent

from substanced.property import PropertySheet
from substanced.schema import Schema
from substanced.content import content

class DocumentSchema(Schema):
    title = colander.SchemaNode(
        colander.String(),
    )


class DocumentBasicPropertySheet(PropertySheet):
    schema = DocumentSchema()

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        return dict(title=self.context.title)

    def set(self, struct):
        self.context.title = struct['title']


@content(
    'Document',
    icon='icon-align-left',
    add_view='add_document',
    propertysheets=(
        ('Basic', DocumentBasicPropertySheet),
        ),
    )
class Document(Persistent):
    def __init__(self, title):
        self.title = title
