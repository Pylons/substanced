from pyramid.exceptions import ConfigurationError
from pyramid.security import (
    Allow,
    ALL_PERMISSIONS,
    )

import colander

from zope.interface import implementer

from ..interfaces import IRoot

from ..content import content
from ..folder import Folder
from ..objectmap import ObjectMap
from ..property import PropertySheet
from ..schema import Schema
from ..util import (
    oid_of,
    change_acl,
    )

class RootSchema(Schema):
    """ The schema representing site properties. """
    sdi_title = colander.SchemaNode(
        colander.String(),
        missing='',
        )

class RootPropertySheet(PropertySheet):
    schema = RootSchema()

@content(
    'Root',
    icon='icon-home',
    propertysheets = (
        ('', RootPropertySheet),
        ),
    after_create='after_create',
    )
@implementer(IRoot)
class Root(Folder):
    """ An object representing the root of a Substance D application (the
    object represented in the root of the SDI).  It is a subclass of
    :class:`substanced.folder.Folder`.

    When created as the result of ``registry.content.create``, an instance of
    a Root will contain a ``principals`` service.  The principals service
    will contain a user whose name is specified via the
    ``substanced.initial_login`` deployment setting with a password taken
    from the ``substanced.initial_password`` setting.  This user will also be
    a member of an ``admins`` group.  The ``admins`` group will be granted
    the ``ALL_PERMISSIONS`` special permission in the root.

    If this class is created by hand, its ``after_create`` method
    must be called manually to set up the services, user, and group.
    """
    sdi_title = ''

    def __init__(self):
        Folder.__init__(self)
        self.__objectmap__ = ObjectMap(self)
        self.__objectmap__.add(self, ('',))

    def after_create(self, inst, registry):
        settings = registry.settings
        password = settings.get('substanced.initial_password')
        if password is None:
            raise ConfigurationError(
                'You must set a substanced.initial_password '
                'in your configuration file'
                )
        login = settings.get('substanced.initial_login', 'admin')
        email = settings.get('substanced.initial_email', 'admin@example.com')
        # side effect of ObjectMap constructor: it sets the ``__objectmap__``
        # attribute of the argument you pass it.
        principals = registry.content.create('Principals')
        # prevent SDI deletion/renaming of root principals service
        principals.__sdi_deletable__ = False
        self.add_service('principals', principals, registry=registry)
        user = principals.add_user(login, password, email, registry=registry)
        admins = principals.add_group('admins', registry=registry)
        admins.memberids.connect([user])
        change_acl(
            self,
            [(Allow, oid_of(admins), ALL_PERMISSIONS)],
            registry=registry,
            )

