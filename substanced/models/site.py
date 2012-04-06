import transaction
import colander

from zope.interface import implementer

from pyramid_zodbconn import get_connection

from ..interfaces import ISite
from ..objectmap import ObjectMap
from ..catalog import Catalog
from ..schema import Schema

from .folder import Folder

class SiteSchema(Schema):
    name = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())

@implementer(ISite)
class Site(Folder):
    
    __propschema__ = SiteSchema()
    
    name = ''
    description = ''

    def __init__(self):
        Folder.__init__(self)
        self.objectmap = ObjectMap(self)
        self.catalog = Catalog(self)

    def get_properties(self):
        return dict(name=self.name, description=self.description)

    def set_properties(self, struct):
        self.name = struct['name']
        self.description = struct['description']
    
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

