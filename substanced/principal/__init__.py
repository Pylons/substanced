import random
import string

from persistent import Persistent
from cryptacular.bcrypt import BCRYPTPasswordManager

from zope.interface import (
    Interface,
    implementer,
    )

import colander
import deform
import deform.widget
import deform_bootstrap.widget

from pyramid.renderers import render
from pyramid.security import (
    Allow,
    Everyone,
    )
from pyramid.threadlocal import get_current_registry

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from ..interfaces import (
    IUser,
    IGroup,
    IUsers,
    IGroups,
    IPrincipals,
    IPasswordResets,
    IPasswordReset,
    )

from ..content import (
    content,
    service,
    find_service,
    )
from ..schema import Schema
from ..folder import Folder
from ..util import oid_of
from ..property import PropertySheet
from ..objectmap import (
    find_objectmap,
    multireference_targetid_property,
    multireference_target_property,
    multireference_sourceid_property,
    multireference_source_property,
    )

class UserToGroup(Interface):
    """ The reference type used to store users-to-groups references in the
    object map"""

def _gen_random_token():
    length = random.choice(range(10, 16))
    chars = string.letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@service(
    'Principals',
    service_name='principals',
    icon='icon-lock',
    after_create='after_create',
    add_view='add_principals_service',
    )
@implementer(IPrincipals)
class Principals(Folder):
    """ Service object representing a collection of principals.  Inherits
    from :class:`substanced.folder.Folder`.

    If this object is created via
    :meth:`substanced.content.ContentRegistry.create`, the instance will
    contain three subobjects:

      ``users``

         an instance of the content type `Users``

      ``groups``

         an instance of the content type ``Groups``
         
      ``resets``

         an instance of the content type ``Password Resets``

    If however, an instance of this class is created directly (as opposed to
    being created via the ``registry.content.create`` API), you'll need to
    call its ``after_create`` method manually after you've created it
    to cause the content subobjects described above to be added to it.
    """
    def __sd_addable__(self, introspectable):
        ct = introspectable.get('content_type')
        if ct in ('Users', 'Groups', 'Password Resets'):
            return True
        return False
        
    def after_create(self, inst, registry):
        users = registry.content.create('Users')
        groups = registry.content.create('Groups')
        resets = registry.content.create('Password Resets')
        users.__sd_deletable__ = False
        groups.__sd_deletable__ = False
        resets.__sd_deletable__ = False
        self['users'] = users
        self['groups'] = groups
        self['resets'] = resets

    def add_user(self, login, *arg, **kw):
        """ Add a user to this principal service using the login ``login``.
        ``*arg`` and ``**kw`` are passed along to
        ``registry.content.create('User')``"""
        registry = kw.pop('registry', None)
        if registry is None:
            registry = get_current_registry()
        user = registry.content.create('User', *arg, **kw)
        self['users'][login] = user
        return user

    def add_group(self, name, *arg, **kw):
        """ Add a group to this principal service using the name ``name``.
        ``*arg`` and ``**kw`` are passed along to
        ``registry.content.create('Group')``"""
        registry = kw.pop('registry', None)
        if registry is None:
            registry = get_current_registry()
        group = registry.content.create('Group', *arg, **kw)
        self['groups'][name] = group
        return group

    def add_reset(self, user, *arg, **kw):
        """ Add a password reset to this principal service for the user
        ``user`` (either a user object or a user id).  ``name``.  ``*arg``
        and ``**kw`` are passed along to ``registry.content.create('Password
        Reset')``"""
        registry = kw.pop('registry', None)
        if registry is None:
            registry = get_current_registry()
        while 1:
            token = _gen_random_token()
            if not token in self:
                break
        reset = registry.content.create('Password Reset', *arg, **kw)
        self['resets'][token] = reset
        reset.__acl__ = [(Allow, Everyone, ('sdi.view',))]
        objectmap = find_objectmap(self)
        objectmap.connect(user, reset, UserToPasswordReset)
        return reset

@content(
    'Users',
    icon='icon-list-alt'
    )
@implementer(IUsers)
class Users(Folder):
    """ Object representing a collection of users.  Inherits from
    :class:`substanced.folder.Folder`.  Contains objects of content type
    'User'."""
    def __sd_addable__(self, introspectable):
        return introspectable.get('content_type') == 'User'

@content(
    'Groups',
    icon='icon-list-alt'
    )
@implementer(IGroups)
class Groups(Folder):
    """ Object representing a collection of groups.  Inherits from
    :class:`substanced.folder.Folder`.  Contains objects of content type 'Group'
    """
    def __sd_addable__(self, introspectable):
        return introspectable.get('content_type') == 'Group'

@colander.deferred
def groupname_validator(node, kw):
    request = kw['request']
    context = request.context
    adding = not request.registry.content.istype(context, 'Group')
    def exists(node, value):
        principals = find_service(context, 'principals')
        if adding:
            try:
                context.check_name(value)
            except Exception as e:
                raise colander.Invalid(node, e.args[0], value)
        else:
            groups = principals['groups']
            if value != context.__name__:
                try:
                    groups.check_name(value)
                except Exception as e:
                    raise colander.Invalid(node, e.args[0], value)

        users = principals['users']
        if value in users:
            raise colander.Invalid(node, 'User named "%s" already exists' % 
                                   value)
        
    return colander.All(
        colander.Length(min=1, max=100),
        exists,
        )

@colander.deferred
def members_widget(node, kw):
    request = kw['request']
    principals = find_service(request.context, 'principals')
    values = [(str(oid_of(user)), name) for name, user in 
              principals['users'].items()]
    widget = deform_bootstrap.widget.ChosenMultipleWidget(values=values)
    return widget
    
class GroupSchema(Schema):
    """ The property schema for :class:`substanced.principal.Group`
    objects."""
    name = colander.SchemaNode(
        colander.String(),
        validator=groupname_validator,
        )
    description = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=100),
        missing='',
        )
    members = colander.SchemaNode(
        deform.Set(allow_empty=True),
        widget=members_widget,
        missing=colander.null,
        preparer=lambda users: set(map(int, users)),
        )

class GroupPropertySheet(PropertySheet):
    schema = GroupSchema()
    
    def get(self):
        context = self.context
        props = {}
        props['description'] = context.description
        props['name'] = context.__name__
        member_strs = map(str, context.memberids)
        props['members'] = member_strs
        return props

    def set(self, struct):
        context = self.context
        if struct['description']:
            context.description = struct['description']
        newname = struct['name']
        oldname = context.__name__
        if newname != oldname:
            parent = context.__parent__
            parent.rename(oldname, newname)
        context.memberids.clear()
        context.memberids.connect(struct['members'])

@content(
    'Group',
    icon='icon-th-list',
    add_view='add_group',
    tab_order=('properties',),
    propertysheets = (
        ('', GroupPropertySheet),
        )
    )
@implementer(IGroup)
class Group(Folder):
    """ Represents a group.  """
    def __init__(self, description=''):
        Folder.__init__(self)
        self.description = description

    memberids = multireference_targetid_property(UserToGroup)
    members = multireference_target_property(UserToGroup)

@colander.deferred
def login_validator(node, kw):
    request = kw['request']
    context = request.context
    adding = not request.registry.content.istype(context, 'User')
    def exists(node, value):
        principals = find_service(context, 'principals')
        if adding:
            try:
                context.check_name(value)
            except Exception as e:
                raise colander.Invalid(node, e.args[0], value)
        else:
            users = principals['users']
            if value != context.__name__:
                try:
                    users.check_name(value)
                except Exception as e:
                    raise colander.Invalid(node, e.args[0], value)

        groups = principals['groups']
        if value in groups:
            raise colander.Invalid(node, 'Group named "%s" already exists' % 
                                   value)
        
    return colander.All(
        colander.Length(min=1, max=100),
        exists,
        )

@colander.deferred
def groups_widget(node, kw):
    request = kw['request']
    principals = find_service(request.context, 'principals')
    values = [(str(oid_of(group)), name) for name, group in 
              principals['groups'].items()]
    widget = deform_bootstrap.widget.ChosenMultipleWidget(values=values)
    return widget

class UserSchema(Schema):
    """ The property schema for :class:`substanced.principal.User`
    objects."""
    login = colander.SchemaNode(
        colander.String(),
        validator=login_validator,
        )
    email = colander.SchemaNode(
        colander.String(),
        validator=colander.All(colander.Email(), colander.Length(max=100)),
        )
    groups = colander.SchemaNode(
        deform.Set(allow_empty=True),
        widget=groups_widget,
        missing=colander.null,
        preparer=lambda groups: set(map(int, groups)),
        )

class UserPropertySheet(PropertySheet):
    schema = UserSchema()
    
    def get(self):
        context = self.context
        props = {}
        props['email'] = context.email
        props['login'] = context.__name__
        props['groups'] = map(str, context.groupids)
        return props

    def set(self, struct):
        context = self.context
        context.email = struct['email']
        newname = struct['login']
        oldname = context.__name__
        if newname != oldname:
            parent = context.__parent__
            parent.rename(oldname, newname)
        context.groupids.clear()
        context.groupids.connect(struct['groups'])

@content(
    'User',
    icon='icon-user',
    add_view='add_user',
    tab_order=('properties',),
    propertysheets = (
        ('', UserPropertySheet),
        )
    )
@implementer(IUser)
class User(Folder):
    """ Represents a user.  """

    pwd_manager = BCRYPTPasswordManager()

    groupids = multireference_sourceid_property(UserToGroup)
    groups = multireference_source_property(UserToGroup)

    def __init__(self, password, email):
        Folder.__init__(self)
        self.password = self.pwd_manager.encode(password)
        self.email = email

    def check_password(self, password):
        """ Checks if the plaintext password passed as ``password`` matches
        this user's stored, encrypted password.  Returns ``True`` or
        ``False``."""
        return self.pwd_manager.check(self.password, password)

    def set_password(self, password):
        self.password = self.pwd_manager.encode(password)

    def email_password_reset(self, request):
        """ Sends a password reset email."""
        root = request.root
        sitename = getattr(root, 'title', None) or 'Substance D'
        principals = find_service(self, 'principals')
        reset = principals.add_reset(self)
        reseturl = request.application_url + request.mgmt_path(reset)
        message = Message(
            subject = 'Account information for %s' % sitename,
            recipients = [self.email],
            body = render('templates/resetpassword_email.pt',
                          dict(reseturl=reseturl))
            )
        mailer = get_mailer(request)
        mailer.send(message)

class UserToPasswordReset(object):
    pass

@content(
    'Password Resets',
    icon='icon-tags'
    )
@implementer(IPasswordResets)
class PasswordResets(Folder):
    """ Object representing the current set of password reset requests """
    def __sd_addable__(self, introspectable):
        return introspectable.get('content_type') == 'Password Reset'

@content(
    'Password Reset',
    icon='icon-tag'
    )
@implementer(IPasswordReset)
class PasswordReset(Persistent):
    """ Object representing the a single password reset request """
    def reset_password(self, password):
        objectmap = find_objectmap(self)
        sources = list(objectmap.sources(self, UserToPasswordReset))
        user = sources[0]
        user.set_password(password)
        self.commit_suicide()

    def commit_suicide(self):
        del self.__parent__[self.__name__]

def groupfinder(userid, request):
    """ A Pyramid authentication policy groupfinder callback that uses the
    Substance D principal system to find groups."""
    context = request.context
    objectmap = find_objectmap(context)
    if objectmap is None:
        return None
    user = objectmap.object_for(userid)
    if user is None:
        return None
    return user.groupids

def includeme(config): # pragma: no cover
    config.scan('.')
    
