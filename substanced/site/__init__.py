import transaction
import colander

from zope.interface import implementer

from pyramid.exceptions import ConfigurationError
from pyramid.security import (
    Allow,
    ALL_PERMISSIONS,
    )

from pyramid_zodbconn import get_connection

from ..objectmap import ObjectMap
from ..schema import Schema
from ..folder import Folder
from ..principal import Principals
from ..acl import NO_INHERIT
from ..content import content
from ..util import oid_of
from ..property import PropertySheet
from ..interfaces import ISite

class SiteSchema(Schema):
    """ The schema representing site properties. """
    title = colander.SchemaNode(colander.String(),
                                missing=colander.null)
    description = colander.SchemaNode(colander.String(),
                                      missing=colander.null)

class SitePropertySheet(PropertySheet):
    schema = SiteSchema()

@content(
    'Site',
    icon='icon-home',
    propertysheets = (
        ('', SitePropertySheet),
        )
    )
@implementer(ISite)
class Site(Folder):
    """ An object representing the root of a Substance D site.  Contains
    ``objectmap`` and ``principals`` services.  Initialize with an initial
    login name and password: the resulting user will be granted all
    permissions."""
    title = ''
    description = ''

    def __init__(self, initial_login, initial_email, initial_password):
        Folder.__init__(self)
        objectmap = ObjectMap()
        principals = Principals()
        self.add_service('objectmap', objectmap)
        self.add_service('principals', principals)
        user = principals['users'].add_user(
            initial_login, initial_password, initial_email
            )
        group = principals['groups'].add_group('admins')
        group.connect(user)
        objectmap.add(self, ('',))
        self.__acl__ = [(Allow, oid_of(group), ALL_PERMISSIONS)]
        self['__services__'].__acl__ = [
            (Allow, oid_of(group), ALL_PERMISSIONS),
            NO_INHERIT,
            ]

    @classmethod
    def root_factory(cls, request, transaction=transaction, 
                     get_connection=get_connection):
        """ A classmethod which can be used as a Pyramid ``root_factory``.
        It accepts a request and returns an instance of Site."""
        # this is a classmethod so that it works when Site is subclassed.
        conn = get_connection(request)
        zodb_root = conn.root()
        if not 'app_root' in zodb_root:
            settings = request.registry.settings
            password = settings.get(
                'substanced.initial_password')
            if password is None:
                raise ConfigurationError(
                    'You must set a substanced.initial_password '
                    'in your configuration file')
            username = settings.get(
                'substanced.initial_login', 'admin')
            email = settings.get(
                'substanced.initial_email', 'admin@example.com')
            app_root = cls(username, email, password)
            zodb_root['app_root'] = app_root
            transaction.commit()
        return zodb_root['app_root']

def includeme(config): # pragma: no cover
    YEAR = 86400 * 365
    config.add_static_view('sitestatic', 'substanced.site:static',
                           cache_max_age=YEAR)
    config.scan('.')
