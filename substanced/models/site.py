import transaction
import colander

from zope.interface import implementer

from pyramid_zodbconn import get_connection

from ..interfaces import ISite
from ..objectmap import ObjectMap
from ..catalog import Catalog
from ..sdi import Schema

from .folder import Folder

class SiteSchema(Schema):
    name = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())

@implementer(ISite)
class Site(Folder):
    name = ''
    description = ''
    __schema__ = SiteSchema()
    def __init__(self):
        Folder.__init__(self)
        self.objectmap = ObjectMap()
        self.catalog = Catalog(self)
    
    @classmethod
    def root_factory(cls, request, transaction=transaction, 
                     get_connection=get_connection):
        # this is a classmethod so that it works when Site is subclassed.
        conn = get_connection(request)
        zodb_root = conn.root()
        if not 'app_root' in zodb_root:
            app_root = cls()
            zodb_root['app_root'] = app_root
            transaction.commit()
        return zodb_root['app_root']

