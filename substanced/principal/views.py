import colander
import deform.widget

from pyramid.httpexceptions import HTTPFound

from ..form import FormView
from ..sdi import mgmt_view
from ..schema import Schema
from ..interfaces import (
    IUsers,
    IUser,
    IGroups,
    IGroup,
    )

from . import (
    UserSchema,
    GroupSchema,
    )

@mgmt_view(context=IUsers, name='add_user', permission='sdi.add-user', 
           renderer='substanced.sdi:templates/form.pt', tab_condition=False)
class AddUserView(FormView):
    title = 'Add User'
    schema = UserSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('login')
        groups = appstruct.pop('groups')
        user = registry.content.create(IUser, **appstruct)
        self.request.context[name] = user
        user.connect(*groups)
        return HTTPFound(self.request.mgmt_path(user, '@@properties'))

@colander.deferred
def password_validator(node, kw):
    """ Returns a ``colander.Function`` validator that uses the context (user)
    to validate the password."""
    context = kw['request'].context
    return colander.Function(
        lambda pwd: context.check_password(pwd),
        'Invalid password'
        )

@mgmt_view(context=IGroups, name='add_group', permission='sdi.add-group', 
           renderer='substanced.sdi:templates/form.pt', tab_condition=False)
class AddGroupView(FormView):
    title = 'Add Group'
    schema = GroupSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('name')
        members = appstruct.pop('members')
        group = registry.content.create(IGroup, **appstruct)
        self.request.context[name] = group
        group.connect(*members)
        return HTTPFound(self.request.mgmt_path(group, '@@properties'))

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


@mgmt_view(context=IUser, name='change_password', tab_title='Change Password',
           permission='sdi.change-password',
           renderer='substanced.sdi:templates/form.pt')
class ChangePasswordView(FormView):
    title = 'Change Password'
    schema = UserPasswordSchema()
    buttons = ('change',)

    def change_success(self, appstruct):
        user = self.request.context
        password = appstruct['password']
        user.set_password(password)
        self.request.session.flash('Password changed')
        return HTTPFound(self.request.mgmt_path(user, '@@change_password'))
