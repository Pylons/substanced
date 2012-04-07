import transaction
import colander

from zope.interface import implementer

from pyramid.exceptions import ConfigurationError
from pyramid.security import (
    Allow,
    ALL_PERMISSIONS,
    )

from pyramid_zodbconn import get_connection

from ..interfaces import ISite
from ..objectmap import ObjectMap
from ..catalog import Catalog
from ..principal import Principals
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

    def __init__(self, initial_login, initial_password):
        Folder.__init__(self)
        self.add_service('objectmap', ObjectMap())
        self.add_service('catalog', Catalog())
        self.add_service('principals', Principals())
        user = self.get_service('principals')['users'].add_user(
            initial_login, initial_password)
        self.get_service('catalog').refresh()
        self.__acl__ = [(Allow, user.__objectid__, ALL_PERMISSIONS)]

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

