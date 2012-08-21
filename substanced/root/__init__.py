import colander

from zope.interface import implementer

from ..schema import Schema
from ..folder import Folder
from ..content import content
from ..property import PropertySheet
from ..interfaces import IRoot

class RootSchema(Schema):
    """ The schema representing site properties. """
    sdi_title = colander.SchemaNode(
        colander.String(),
        missing=colander.null
        )

class RootPropertySheet(PropertySheet):
    schema = RootSchema()

@content(
    'Root',
    icon='icon-home',
    propertysheets = (
        ('', RootPropertySheet),
        )
    )
@implementer(IRoot)
class Root(Folder):
    """ An object representing the root of a Substance D application (the
    object represented in the root of the SDI).  Contains ``objectmap`` and
    ``principals`` services when first initialized.

    The constructor of this class accepts a ``request`` object which should
    be a Pyramid request.
    """
    sdi_title = ''
    def __init__(self, request):
        Folder.__init__(self)

def includeme(config): # pragma: no cover
    config.scan('.')
