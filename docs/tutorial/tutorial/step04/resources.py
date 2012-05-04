import colander

from persistent import Persistent

from substanced.schema import Schema
from substanced.content import content

class DocumentSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        )
    title = colander.SchemaNode(
        colander.String(),
    )

@content(
    'Document',
    icon='icon-align-left',
    add_view='add_document',
    )
class Document(Persistent):
    def __init__(self, title):
        self.title = title
