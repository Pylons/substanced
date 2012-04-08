from BTrees.IFBTree import IFTreeSet

from zope.interface import implementer

import colander
import deform
import deform.widget

from cryptacular.bcrypt import BCRYPTPasswordManager
pwd_manager = BCRYPTPasswordManager()

from pyramid.events import subscriber
from pyramid.renderers import render

from ..interfaces import (
    IUser,
    IGroup,
    IUsers,
    IGroups,
    IPrincipals,
    IPrincipalContent,
    IObjectAddedEvent,
    IObjectWillBeRemovedEvent,
    IObjectModifiedEvent,
    )

from ..schema import Schema
from ..service import find_service
from ..content import content
from ..folder import Folder

@implementer(IPrincipals)
class Principals(Folder):
    def __init__(self):
        Folder.__init__(self)
        self['users'] = Users()
        self['groups'] = Groups()

@implementer(IUsers)
class Users(Folder):
    def add_user(self, login, password):
        user = User(password)
        self[login] = user
        return user

@implementer(IGroups)
class Groups(Folder):
    pass

@colander.deferred
def groupname_validator(node, kw):
    context = kw['request'].context
    adding = not IGroup.providedBy(context)
    def exists(node, value):
        principals = find_service(context, 'principals')
        invalid = colander.Invalid(node, 'Group named "%s" already exists' % 
                                   value)
        if adding:
            if value in context:
                raise invalid
        else:
            groups = principals['groups']
            if value != context.__name__ and value in groups:
                raise invalid

        users = principals['users']
        if value in users:
            raise colander.Invalid(node, 'User named "%s" already exists' % 
                                   value)
        
    return colander.All(
        colander.Length(min=4, max=100),
        exists,
        )

class MembersWidget(deform.widget.Widget):
    def serialize(self, field, cstruct, readonly=False):
        result = render('templates/members.pt', {'cstruct':cstruct})
        return result

    def deserialize(self, field, pstruct):
        return colander.null

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
        widget=MembersWidget(),
        missing=colander.null,
        )

@content(IGroup, IPrincipalContent)
class Group(Folder):
    description = ''
    tab_order = ('properties',)
    __propschema__ = GroupSchema()

    def __init__(self, description):
        Folder.__init__(self)
        self.description = description
        self.members = IFTreeSet()

    def get_properties(self):
        props = {}
        props['description'] = self.description
        props['name'] = self.__name__
        members = [ x.__name__ for x in self.get_members() ]
        props['members'] = members # readonly
        return props

    def set_properties(self, struct):
        if struct['description']:
            self.description = struct.description
        name = struct['name']
        if name != self.__name__:
            parent = self.__parent__
            del parent[self.__name__]
            parent[name] = self # will raise exc if already exists

    def get_members(self):
        L = []
        objectmap = find_service(self, 'objectmap')
        for memberid in self.members:
            member = objectmap.object_for(memberid)
            if member is not None:
                L.append(member)
        return L

@colander.deferred
def login_validator(node, kw):
    context = kw['request'].context
    adding = not IUser.providedBy(context)
    def exists(node, value):
        principals = find_service(context, 'principals')
        invalid = colander.Invalid(node, 'Login named "%s" already exists' % 
                                   value)
        if adding:
            if value in context:
                raise invalid
        else:
            users = principals['users']
            if value != context.__name__ and value in users:
                raise invalid

        groups = principals['groups']
        if value in groups:
            raise colander.Invalid(node, 'Group named "%s" already exists' % 
                                   value)
        
    return colander.All(
        colander.Length(min=4, max=100),
        exists,
        )

@colander.deferred
def groups_widget(node, kw):
    request = kw['request']
    principals = find_service(request.context, 'principals')
    values = [(str(group.__objectid__), name) for name, group in 
              principals['groups'].items()]
    widget = deform.widget.CheckboxChoiceWidget(values=values)
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

@content(IUser, IPrincipalContent)
class User(Folder):

    tab_order = ('properties',)

    __propschema__ = UserSchema()
    
    def __init__(self, password, email='', security_question='',
                 security_answer='', groups=()):
        Folder.__init__(self)
        self.password = pwd_manager.encode(password)
        self.email = email
        self.security_question = security_question
        self.security_answer = security_answer
        self.groups = IFTreeSet(groups)

    def check_password(self, password):
        if pwd_manager.check(self.password, password):
            return True
        return False

    def set_properties(self, struct):
        password = struct['password']
        if password != NO_CHANGE:
            self.password = pwd_manager.encode(password)
        for attr in ('email', 'security_question', 'security_answer'):
            setattr(self, attr, struct[attr])
        login = struct['login']
        if login != self.__name__:
            parent = self.__parent__
            del parent[self.__name__]
            parent[login] = self # will raise exc if already exists
        newgroups = IFTreeSet(map(int, struct['groups']))
        self.groups = newgroups

    def get_properties(self):
        props = {}
        for attr in ('email', 'security_question', 'security_answer'):
            props[attr] = getattr(self, attr)
        props['password'] = NO_CHANGE
        props['login'] = self.__name__
        props['groups'] = [str(x) for x in self.groups]
        return props

    def get_groups(self):
        L = []
        objectmap = find_service(self, 'objectmap')
        for groupid in self.groups:
            group = objectmap.object_for(groupid)
            if group is not None:
                L.append(group)
        return L

@subscriber([IUser, IObjectAddedEvent])
def user_added(user, event):
    principals = find_service(user, 'principals')
    groups = principals['groups']
    login = user.__name__
    if login in groups:
        raise ValueError(
            'Cannot add a user with a login name the same as the '
            'group name %s' % login
            )
    objectmap = find_service(user, 'objectmap')
    userid = user.__objectid__
    for groupid in user.groups:
        group = objectmap.object_for(groupid)
        if group is not None:
            group.members.insert(userid)

@subscriber([IGroup, IObjectAddedEvent])
def group_added(group, event):
    principals = find_service(group, 'principals')
    users = principals['users']
    name = group.__name__
    if name in users:
        raise ValueError(
            'Cannot add a group with a name the same as the '
            'user with the login name %s' % name
            )
    groupid = group.__objectid__
    objectmap = find_service(group, 'objectmap')
    for userid in group.members:
        user = objectmap.object_for(userid)
        if user is not None:
            user.groups.insert(groupid)
    
@subscriber([IUser, IObjectWillBeRemovedEvent])
def user_removed(user, event):
    userid = user.__objectid__
    principals = find_service(user, 'principals')
    groups = principals['groups']
    for group in groups.values():
        if userid in group.members:
            group.members.remove(userid)

@subscriber([IGroup, IObjectWillBeRemovedEvent])
def group_removed(group, event):
    groupid = group.__objectid__
    principals = find_service(group, 'principals')
    users = principals['users']
    for user in users.values():
        if groupid in user.groups:
            user.groups.remove(groupid)

#from zope.interface import Interface

@subscriber([IUser, IObjectModifiedEvent])
def user_modified(user, event):
    userid = user.__objectid__
    principals = find_service(user, 'principals')
    groups = principals['groups']
    for group in groups.values():
        groupid = group.__objectid__
        if groupid in user.groups:
            if not userid in group.members:
                group.members.insert(userid)
        else:
            if userid in group.members:
                group.members.remove(userid)

@subscriber([IGroup, IObjectModifiedEvent])
def group_modified(group, event):
    groupid = group.__objectid__
    principals = find_service(group, 'principals')
    users = principals['users']
    for user in users.values():
        userid = user.__objectid__
        if userid in group.members:
            if not groupid in user.groups:
                user.groups.insert(groupid)
        else:
            if groupid in user.groups:
                user.groups.remove(groupid)

def groupfinder(userid, request):
    context = request.context
    objectmap = find_service(context, 'objectmap')
    user = objectmap.object_for(userid)
    if user is None:
        return None
    return list(user.groups)

def includeme(config): # pragma: no cover
    config.scan('substanced.principal')
    
