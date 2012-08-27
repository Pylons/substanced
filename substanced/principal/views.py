import colander
import deform.widget

from pyramid.httpexceptions import HTTPFound

from ..form import FormView
from ..sdi import mgmt_view
from ..schema import Schema
from ..content import find_service

from ..interfaces import (
    IUsers,
    IUser,
    IGroups,
    IPasswordReset,
    )

from . import (
    UserSchema,
    GroupSchema,
    )

class AddUserSchema(UserSchema):
    password = colander.SchemaNode(
        colander.String(),
        widget = deform.widget.CheckedPasswordWidget(),
        )

@mgmt_view(
    content_type='Services',
    name='add_principals_service',
    tab_condition=False,
    permission='sdi.add-services',
    )
def add_principals_service(context, request):
    service = request.registry.content.create('Principals')
    context['principals'] = service
    return HTTPFound(location=request.mgmt_path(context))

@mgmt_view(
    context=IUsers,
    name='add_user',
    permission='sdi.add-user', 
    renderer='substanced.sdi:templates/form.pt',
    tab_condition=False
    )
class AddUserView(FormView):
    title = 'Add User'
    schema = AddUserSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('login')
        groups = appstruct.pop('groups')
        user = registry.content.create('User', **appstruct)
        self.context[name] = user
        user.connect(*groups)
        return HTTPFound(self.request.mgmt_path(user, '@@properties'))

@mgmt_view(
    context=IGroups,
    name='add_group',
    permission='sdi.add-group', 
    renderer='substanced.sdi:templates/form.pt',
    tab_condition=False
    )
class AddGroupView(FormView):
    title = 'Add Group'
    schema = GroupSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('name')
        members = appstruct.pop('members')
        group = registry.content.create('Group', **appstruct)
        self.context[name] = group
        group.connect(*members)
        return HTTPFound(self.request.mgmt_path(group, '@@properties'))

@colander.deferred
def password_validator(node, kw):
    """ Returns a ``colander.Function`` validator that uses the context (user)
    to validate the password."""
    context = kw['context']
    return colander.Function(
        lambda pwd: context.check_password(pwd),
        'Invalid password'
        )

class UserPasswordSchema(Schema):
    """ The schema for validating password change requests."""
    old_password = colander.SchemaNode(
        colander.String(),
        validator=password_validator,
        widget = deform.widget.PasswordWidget(),
        )
    password = colander.SchemaNode(
        colander.String(),
        title='New Password',
        validator=colander.Length(min=3, max=100),
        widget = deform.widget.CheckedPasswordWidget(),
        )


@mgmt_view(
    context=IUser,
    name='change_password',
    tab_title='Change Password',
    permission='sdi.change-password',
    renderer='substanced.sdi:templates/form.pt'
    )
class ChangePasswordView(FormView):
    title = 'Change Password'
    schema = UserPasswordSchema()
    buttons = ('change',)

    def change_success(self, appstruct):
        user = self.context
        password = appstruct['password']
        user.set_password(password)
        self.request.session.flash('Password changed', 'success')
        return HTTPFound(self.request.mgmt_path(user, '@@change_password'))

@colander.deferred
def login_validator(node, kw):
    context = kw['context']
    def _login_validator(node, value):
        principals = find_service(context, 'principals')
        users = principals['users']
        if not value in users:
            raise colander.Invalid(node, 'No such user %s' % value)
    return _login_validator

class ResetRequestSchema(Schema):
    """ The schema for validating password reset requests."""
    login = colander.SchemaNode(
        colander.String(),
        validator = login_validator,
        )

@mgmt_view(
    name='resetpassword',
    tab_condition=False,
    renderer='substanced.sdi:templates/form.pt'
    )
class ResetRequestView(FormView):
    title = 'Request Password Reset'
    schema = ResetRequestSchema()
    buttons = ('send',)

    def send_success(self, appstruct):
        request = self.request
        context = self.context
        login = appstruct['login']
        principals = find_service(context, 'principals')
        users = principals['users']
        user = users[login]
        user.email_password_reset(request)
        request.session.flash('Emailed password reset instructions', 'success')
        home = request.mgmt_path(request.root)
        return HTTPFound(location=home)
        
class ResetSchema(Schema):
    """ The schema for validating password reset requests."""
    new_password = colander.SchemaNode(
        colander.String(),
        validator = colander.Length(min=3, max=100),
        widget = deform.widget.CheckedPasswordWidget(),
        )

@mgmt_view(
    context=IPasswordReset,
    name='',
    tab_condition=False,
    renderer='substanced.sdi:templates/form.pt'
    )
class ResetView(FormView):
    title = 'Reset Password'
    schema = ResetSchema()
    buttons = ('reset',)
    
    def reset_success(self, appstruct):
        request = self.request
        context = self.context
        context.reset_password(appstruct['new_password'])
        request.session.flash('Password reset, you may now log in', 'success')
        home = request.mgmt_path(request.root)
        return HTTPFound(location=home)
