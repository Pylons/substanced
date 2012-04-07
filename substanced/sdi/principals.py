from ..form import FormView

from pyramid.httpexceptions import HTTPFound

from ..interfaces import (
    IUsers,
    IUser,
    IGroups,
    IGroup,
    IPrincipalContent,
    )

from . import mgmt_view

from ..principal import (
    UserSchema,
    GroupSchema,
    )

@mgmt_view(context=IUsers, name='add', permission='add user', 
           renderer='templates/form.pt')
class AddUserView(FormView):
    title = 'Add User'
    schema = UserSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('login')
        user = registry.content[IPrincipalContent].create(IUser, **appstruct)
        self.request.context[name] = user
        return HTTPFound(self.request.mgmt_path(user, '@@properties'))

@mgmt_view(context=IGroups, name='add', permission='add group', 
           renderer='templates/form.pt')
class AddGroupView(FormView):
    title = 'Add Group'
    schema = GroupSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('name')
        appstruct.pop('members')
        group = registry.content[IPrincipalContent].create(IGroup, **appstruct)
        self.request.context[name] = group
        return HTTPFound(self.request.mgmt_path(group, '@@properties'))
    
