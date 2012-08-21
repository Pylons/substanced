import transaction
from pyramid.exceptions import ConfigurationError
from pyramid.security import (
    Allow,
    ALL_PERMISSIONS,
    )
from pyramid_zodbconn import get_connection

from .event import RootCreated
from .util import oid_of

def root_factory(request, t=transaction, g=get_connection):
    """ A function which can be used as a Pyramid ``root_factory``.  It
    accepts a request and returns an instance of the ``Root`` content type."""
    # accepts "t" and "g" for unit testing purposes only
    conn = g(request)
    zodb_root = conn.root()
    if not 'app_root' in zodb_root:
        registry = request.registry
        settings = registry.settings
        password = settings.get('substanced.initial_password')
        if password is None:
            raise ConfigurationError(
                'You must set a substanced.initial_password '
                'in your configuration file'
                )
        login = settings.get('substanced.initial_login', 'admin')
        email = settings.get('substanced.initial_email', 'admin@example.com')
        app_root = registry.content.create('Root', request)
        objectmap = registry.content.create('Object Map')
        # prevent SDI deletion/renaming of objectmap
        objectmap.__sd_deletable__ = False
        app_root.add_service('objectmap', objectmap)
        principals = registry.content.create('Principals')
        # prevent SDI deletion/renaming of root principals service
        principals.__sd_deletable__ = False
        app_root.add_service('principals', principals)
        user = principals['users'].add_user(login, password, email)
        admins = principals['groups'].add_group('admins')
        admins.connect(user)
        app_root.__acl__ = [
            (Allow, oid_of(admins), ALL_PERMISSIONS)
            ]
        # prevent SDI deletion/renaming of root services folder
        app_root['__services__'].__sd_deletable__ = False
        objectmap.add(app_root, ('',))
        zodb_root['app_root'] = app_root
        created = RootCreated(app_root, request)
        request.registry.notify(created)
        t.commit()
    return zodb_root['app_root']

def includeme(config): # pragma: no cover
    config.include('pyramid_zodbconn')
    config.include('pyramid_mailer')
    config.include('.sdi')
    config.include('.content')
    config.include('.acl')
    config.include('.objectmap')
    config.include('.catalog')
    config.include('.root')
    config.include('.evolution')
    config.include('.folder')
    config.include('.principal')
    config.include('.undo')
    config.include('.property')
    config.include('.widget')
    config.include('.file')
    config.include('.workflow')
