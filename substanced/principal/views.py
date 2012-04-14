from pyramid.httpexceptions import HTTPFound

from ..form import FormView
from ..sdi import mgmt_view
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

@mgmt_view(context=IUsers, name='add_user', permission='add user', 
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

@mgmt_view(context=IGroups, name='add_group', permission='add group', 
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
    
