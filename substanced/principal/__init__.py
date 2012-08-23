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

class UserToGroup(Interface):
    """ The reference type used to store users-to-groups references in the
    object map"""

@service(
    'Principals',
    service_name='principals',
    icon='icon-lock',
    after_create='after_create',
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
    call its ``after_create`` method manually after you've created it to
    cause the content subobjects described above to be added to it.
    """
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

@content(
    'Users',
    icon='icon-list-alt'
    )
@implementer(IUsers)
class Users(Folder):
    """ Object representing a collection of users.  Inherits from
    :class:`substanced.folder.Folder`.  Contains objects of content type
    'User'."""
    def add_user(self, login, *arg, **kw):
        registry = kw.pop('registry', None)
        if registry is None:
            registry = get_current_registry()
        user = registry.content.create('User', *arg, **kw)
        self[login] = user
        return user

@content(
    'Groups',
    icon='icon-list-alt'
    )
@implementer(IGroups)
class Groups(Folder):
    """ Object representing a collection of groups.  Inherits from
    :class:`substanced.folder.Folder`.  Contains objects of content type 'Group'
    """
    def add_group(self, name, *arg, **kw):
        registry = kw.pop('registry', None)
        if registry is None:
            registry = get_current_registry()
        group = registry.content.create('Group', *arg, **kw)
        self[name] = group
        return group

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
        member_strs = map(str, context.get_memberids())
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
        context.disconnect()
        context.connect(*struct['members'])

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

    def _resolve_member(self, member_or_memberid):
        objectmap = find_service(self, 'objectmap')
        if oid_of(member_or_memberid, None) is None:
            # it's a group id
            member = objectmap.object_for(member_or_memberid)
        else:
            member = member_or_memberid
        return member

    def get_memberids(self):
        """ Returns a sequence of member ids which belong to this group. """
        objectmap = find_service(self, 'objectmap')
        return objectmap.sourceids(self, UserToGroup)

    def get_members(self):
        """ Returns a generator of member objects which belong to this group. 
        """
        objectmap = find_service(self, 'objectmap')
        return objectmap.sources(self, UserToGroup)

    def connect(self, *members):
        """ Connect this group to one or more user objects or user 
        objectids."""
        objectmap = find_service(self, 'objectmap')
        for memberid in members:
            member = self._resolve_member(memberid)
            if member is not None:
                objectmap.connect(member, self, UserToGroup)

    def disconnect(self, *members):
        """ Disconnect this group from one or more user objects or user 
        objectids."""
        if not members:
            members = self.get_memberids()
        objectmap = find_service(self, 'objectmap')
        for memberid in members:
            member = self._resolve_member(memberid)
            if member is not None:
                objectmap.disconnect(member, self, UserToGroup)

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
        props['groups'] = map(str, context.get_groupids())
        return props

    def set(self, struct):
        context = self.context
        context.email = struct['email']
        newname = struct['login']
        oldname = context.__name__
        if newname != oldname:
            parent = context.__parent__
            parent.rename(oldname, newname)
        context.disconnect()
        context.connect(*struct['groups'])

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

    def __init__(self, password, email):
        Folder.__init__(self)
        self.password = self.pwd_manager.encode(password)
        self.email = email

    def _resolve_group(self, group_or_groupid):
        objectmap = find_service(self, 'objectmap')
        if oid_of(group_or_groupid, None) is None:
            # it's a group id
            group = objectmap.object_for(group_or_groupid)
        else:
            group = group_or_groupid
        return group

    def check_password(self, password):
        """ Checks if the plaintext password passed as ``password`` matches
        this user's stored, encrypted passowrd.  Returns ``True`` or
        ``False``."""
        return self.pwd_manager.check(self.password, password)

    def set_password(self, password):
        self.password = self.pwd_manager.encode(password)

    def email_password_reset(self, request):
        """ Sends a password reset email."""
        root = request.root
        sitename = getattr(root, 'title', None) or 'Substance D'
        principals = find_service(self, 'principals')
        resets = principals['resets']
        reset = resets.add_reset(self)
        reseturl = request.application_url + request.mgmt_path(reset)
        message = Message(
            subject = 'Account information for %s' % sitename,
            recipients = [self.email],
            body = render('templates/resetpassword_email.pt',
                          dict(reseturl=reseturl))
            )
        mailer = get_mailer(request)
        mailer.send(message)

    def get_groupids(self, objectmap=None):
        """ Returns a sequence of group ids which this user is a member of. """
        if objectmap is None:
            objectmap = find_service(self, 'objectmap')
        return objectmap.targetids(self, UserToGroup)

    def get_groups(self):
        """ Returns a generator of group objects which this user is a member
        of."""
        objectmap = find_service(self, 'objectmap')
        return objectmap.targets(self, UserToGroup)

    def connect(self, *groups):
        """ Connect this user to one or more group objects or group 
        objectids."""
        objectmap = find_service(self, 'objectmap')
        for groupid in groups:
            group = self._resolve_group(groupid)
            if group is not None:
                objectmap.connect(self, group, UserToGroup)

    def disconnect(self, *groups):
        """ Disconnect this user from one or more group objects or group 
        objectids."""
        if not groups:
            groups = self.get_groupids()
        objectmap = find_service(self, 'objectmap')
        for groupid in groups:
            group = self._resolve_group(groupid)
            if group is not None:
                objectmap.disconnect(self, group, UserToGroup)

class UserToPasswordReset(object):
    pass

@content(
    'Password Resets',
    icon='icon-tags'
    )
@implementer(IPasswordResets)
class PasswordResets(Folder):
    """ Object representing the current set of password reset requests """
    def _gen_random_token(self):
        """ Generates a random token to be used by ``self.add_reset``.
        """
        length = random.choice(range(10, 16))
        chars = string.letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def add_reset(self, user, *arg, **kw):
        registry = kw.pop('registry', None)
        if registry is None:
            registry = get_current_registry()
        while 1:
            token = self._gen_random_token()
            if not token in self:
                break
        reset = registry.content.create('Password Reset', *arg, **kw)
        self[token] = reset
        reset.__acl__ = [(Allow, Everyone, ('sdi.view',))]
        objectmap = find_service(self, 'objectmap')
        objectmap.connect(user, reset, UserToPasswordReset)
        return reset

@content(
    'Password Reset',
    icon='icon-tag'
    )
@implementer(IPasswordReset)
class PasswordReset(Persistent):
    """ Object representing the a single password reset request """
    def reset_password(self, password):
        objectmap = find_service(self, 'objectmap')
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
    objectmap = find_service(context, 'objectmap')
    if objectmap is None:
        return None
    user = objectmap.object_for(userid)
    if user is None:
        return None
    return user.get_groupids(objectmap)

def includeme(config): # pragma: no cover
    config.scan('.')
    
