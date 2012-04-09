import transaction
import colander

from pyramid.exceptions import ConfigurationError
from pyramid.security import (
    Allow,
    ALL_PERMISSIONS,
    )

from pyramid_zodbconn import get_connection

from ..interfaces import ISite
from ..objectmap import ObjectMap
from ..catalog import Catalog
from ..schema import Schema
from ..folder import Folder
from ..principal import (
    Principals,
    NO_INHERIT,
    )
from ..content import content

class SiteSchema(Schema):
    title = colander.SchemaNode(colander.String(),
                                missing=colander.null)
    description = colander.SchemaNode(colander.String(),
                                      missing=colander.null)

@content(ISite, icon='icon-home')
class Site(Folder):
    
    __propschema__ = SiteSchema()
    
    title = ''
    description = ''

    def __init__(self, initial_login, initial_password):
        Folder.__init__(self)
        objectmap = ObjectMap()
        catalog = Catalog()
        principals = Principals()
        self.add_service('objectmap', objectmap)
        self.add_service('catalog', catalog)
        self.add_service('principals', principals)
        user = principals['users'].add_user(initial_login, initial_password)
        catalog.refresh()
        objectmap.add(self, ('',))
        self.__acl__ = [(Allow, user.__objectid__, ALL_PERMISSIONS)]
        self['__services__'].__acl__ = [
            (Allow, user.__objectid__, ALL_PERMISSIONS),
            NO_INHERIT,
            ]

    @classmethod
    def root_factory(cls, request, transaction=transaction, 
                     get_connection=get_connection):
        # this is a classmethod so that it works when Site is subclassed.
        conn = get_connection(request)
        zodb_root = conn.root()
        if not 'app_root' in zodb_root:
            password = request.registry.settings.get(
                'substanced.initial_password')
            if password is None:
                raise ConfigurationError(
                    'You must set a substanced.initial_password '
                    'in your configuration file')
            username = request.registry.settings.get(
                'substanced.initial_login', 'admin')
            app_root = cls(username, password)
            zodb_root['app_root'] = app_root
            transaction.commit()
        return zodb_root['app_root']

def includeme(config): # pragma: no cover
    config.add_content_type(ISite, Site)
