import colander

from zope.interface import implementer

from pyramid.exceptions import ConfigurationError
from pyramid.security import (
    Allow,
    ALL_PERMISSIONS,
    )

from ..objectmap import ObjectMap
from ..schema import Schema
from ..folder import Folder
from ..principal import Principals
from ..acl import NO_INHERIT
from ..content import content
from ..util import oid_of
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
    ``principals`` services.  Initialize with a settings dictionary
    containing an initial login name, email, and password: the resulting user
    will be granted all permissions."""
    sdi_title = ''

    def __init__(self, settings):
        Folder.__init__(self)
        objectmap = ObjectMap()
        principals = Principals()
        self.add_service('objectmap', objectmap)
        self.add_service('principals', principals)
        password = settings.get('substanced.initial_password')
        if password is None:
            raise ConfigurationError(
                'You must set a substanced.initial_password '
                'in your configuration file'
                )
        login = settings.get('substanced.initial_login', 'admin')
        email = settings.get('substanced.initial_email', 'admin@example.com')
        user = principals['users'].add_user(login, password, email)
        group = principals['groups'].add_group('admins')
        group.connect(user)
        objectmap.add(self, ('',))
        self.__acl__ = [
            (Allow, oid_of(group), ALL_PERMISSIONS)
            ]
        self['__services__'].__acl__ = [
            (Allow, oid_of(group), ALL_PERMISSIONS),
            NO_INHERIT,
            ]

def includeme(config): # pragma: no cover
    config.scan('.')
