from cryptacular.bcrypt import BCRYPTPasswordManager
from zope.interface import Interface

import colander
import deform
import deform.widget
import deform_bootstrap.widget

from pyramid.events import subscriber

from ..interfaces import (
    IUser,
    IGroup,
    IUsers,
    IGroups,
    IPrincipal,
    IPrincipals,
    IObjectAddedEvent,
    )

from ..content import content
from ..schema import Schema
from ..service import find_service
from ..folder import Folder
from ..util import oid_of

class UserToGroup(Interface): # reference type
    pass

@content(IPrincipals, icon='icon-lock')
class Principals(Folder):
    def __init__(self):
        Folder.__init__(self)
        self['users'] = Users()
        self['groups'] = Groups()

@content(IUsers, icon='icon-list-alt')
class Users(Folder):
    def add_user(self, login, password):
        user = User(password)
        self[login] = user
        return user

@content(IGroups, icon='icon-list-alt')
class Groups(Folder):
    pass

@colander.deferred
def groupname_validator(node, kw):
    context = kw['request'].context
    adding = not IGroup.providedBy(context)
    def exists(node, value):
        principals = find_service(context, 'principals')
        if adding:
            try:
                context.check_name(value)
            except Exception as e:
                raise colander.Invalid(node, e.message, value)
        else:
            groups = principals['groups']
            if value != context.__name__:
                try:
                    groups.check_name(value)
                except Exception as e:
                    raise colander.Invalid(node, e.message, value)

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

@content(IGroup, icon='icon-th-list', add_view='add_group', name='Group')
class Group(Folder):
    __tab_order__ = ('properties',)
    __propschema__ = GroupSchema()

    def __init__(self, description):
        Folder.__init__(self)
        self.description = description

    def _resolve_member(self, member_or_memberid):
        objectmap = self.get_service('objectmap')
        if oid_of(member_or_memberid, None) is None:
            # it's a group id
            member = objectmap.object_for(member_or_memberid)
        else:
            member = member_or_memberid
        return member

    def get_properties(self):
        props = {}
        props['description'] = self.description
        props['name'] = self.__name__
        member_strs = map(str, self.get_memberids())
        props['members'] = member_strs
        return props

    def set_properties(self, struct):
        if struct['description']:
            self.description = struct['description']
        newname = struct['name']
        oldname = self.__name__
        if newname != oldname:
            parent = self.__parent__
            parent.rename(oldname, newname)
        self.disconnect()
        self.connect(*struct['members'])

    def get_memberids(self):
        objectmap = self.get_service('objectmap')
        return objectmap.sourceids(self, UserToGroup)

    def get_members(self):
        objectmap = self.get_service('objectmap')
        return objectmap.sources(self, UserToGroup)

    def connect(self, *members):
        objectmap = self.get_service('objectmap')
        for memberid in members:
            member = self._resolve_member(memberid)
            if member is not None:
                objectmap.connect(member, self, UserToGroup)

    def disconnect(self, *members):
        if not members:
            members = self.get_memberids()
        objectmap = self.get_service('objectmap')
        for memberid in members:
            member = self._resolve_member(memberid)
            if member is not None:
                objectmap.disconnect(member, self, UserToGroup)

@colander.deferred
def login_validator(node, kw):
    context = kw['request'].context
    adding = not IUser.providedBy(context)
    def exists(node, value):
        principals = find_service(context, 'principals')
        if adding:
            try:
                context.check_name(value)
            except Exception as e:
                raise colander.Invalid(node, e.message, value)
        else:
            users = principals['users']
            if value != context.__name__:
                try:
                    users.check_name(value)
                except Exception as e:
                    raise colander.Invalid(node, e.message, value)

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
    login = colander.SchemaNode(
        colander.String(),
        validator=login_validator,
        )
    email = colander.SchemaNode(
        colander.String(),
        validator=colander.All(colander.Email(), colander.Length(max=100)),
        missing='',
        )
    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=3, max=100),
        widget = deform.widget.CheckedPasswordWidget(),
        )
    security_question = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=200),
        missing='',
        )
    security_answer = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=200),
        missing='',
        )
    groups = colander.SchemaNode(
        deform.Set(allow_empty=True),
        widget=groups_widget,
        missing=colander.null,
        preparer=lambda groups: set(map(int, groups)),
        )

NO_CHANGE = u'\ufffd' * 8

@content(IUser, icon='icon-user', add_view='add_user', name='User')
class User(Folder):

    __tab_order__ = ('properties',)
    __propschema__ = UserSchema()

    pwd_manager = BCRYPTPasswordManager()

    def __init__(self, password, email='', security_question='',
                 security_answer=''):
        Folder.__init__(self)
        self.password = self.pwd_manager.encode(password)
        self.email = email
        self.security_question = security_question
        self.security_answer = security_answer

    def _resolve_group(self, group_or_groupid):
        objectmap = self.get_service('objectmap')
        if oid_of(group_or_groupid, None) is None:
            # it's a group id
            group = objectmap.object_for(group_or_groupid)
        else:
            group = group_or_groupid
        return group

    def check_password(self, password):
        if self.pwd_manager.check(self.password, password):
            return True
        return False

    def get_properties(self):
        props = {}
        for attr in ('email', 'security_question', 'security_answer'):
            props[attr] = getattr(self, attr)
        props['password'] = NO_CHANGE
        props['login'] = self.__name__
        group_strs = map(str, self.get_groupids())
        props['groups'] = group_strs
        return props

    def set_properties(self, struct):
        password = struct['password']
        if password != NO_CHANGE:
            self.password = self.pwd_manager.encode(password)
        for attr in ('email', 'security_question', 'security_answer'):
            setattr(self, attr, struct[attr])
        newname = struct['login']
        oldname = self.__name__
        if newname != oldname:
            parent = self.__parent__
            parent.rename(oldname, newname)
        self.disconnect()
        self.connect(*struct['groups'])

    def get_groupids(self, objectmap=None):
        if objectmap is None:
            objectmap = self.get_service('objectmap')
        return objectmap.targetids(self, UserToGroup)

    def get_groups(self):
        objectmap = self.get_service('objectmap')
        return objectmap.targets(self, UserToGroup)

    def connect(self, *groups):
        objectmap = self.get_service('objectmap')
        for groupid in groups:
            group = self._resolve_group(groupid)
            if group is not None:
                objectmap.connect(self, group, UserToGroup)

    def disconnect(self, *groups):
        if not groups:
            groups = self.get_groupids()
        objectmap = self.get_service('objectmap')
        for groupid in groups:
            group = self._resolve_group(groupid)
            if group is not None:
                objectmap.disconnect(self, group, UserToGroup)

@subscriber([IPrincipal, IObjectAddedEvent])
def principal_added(principal, event):
    # disallow same-named groups and users for human sanity (not because
    # same-named users and groups are disallowed by the system)
    principal_name = principal.__name__
    principals = find_service(principal, 'principals')
    
    if IUser.providedBy(principal):
        groups = principals['groups']
        if principal_name in groups:
            raise ValueError(
                'Cannot add a user with a login name the same as the '
                'group name %s' % principal_name
                )
    else:
        users = principals['users']
        if principal_name in users:
            raise ValueError(
                'Cannot add a group with a name the same as the '
                'user with the login name %s' % principal_name
            )
    
def groupfinder(userid, request):
    context = request.context
    objectmap = find_service(context, 'objectmap')
    if objectmap is None:
        return None
    user = objectmap.object_for(userid)
    if user is None:
        return None
    return user.get_groupids(objectmap)

def includeme(config): # pragma: no cover
    config.scan('substanced.principal')
    
