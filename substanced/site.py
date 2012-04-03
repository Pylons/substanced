import transaction
import colander

from zope.interface import implementer

from pyramid_zodbconn import get_connection

from .interfaces import IDocmapSite
from .docmap import DocumentMap
from .folder import Folder
from .sdi import Schema

class SiteSchema(Schema):
    name = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())

@implementer(IDocmapSite)
class Site(Folder):
    name = ''
    description = ''
    __schema__ = SiteSchema()
    def __init__(self):
        Folder.__init__(self)
        self.docmap = DocumentMap()
    
    @classmethod
    def root_factory(cls, request):
        # this is a classmethod so that it works when Site is subclassed.
        conn = get_connection(request)
        zodb_root = conn.root()
        if not 'app_root' in zodb_root:
            app_root = cls()
            zodb_root['app_root'] = app_root
            transaction.commit()
        return zodb_root['app_root']

