import colander

from pyramid.httpexceptions import HTTPFound
from pyramid.security import has_permission

from ..schema import Schema
from ..form import FormView
from ..sdi import (
    mgmt_view,
    get_batchinfo,
    )

from ..interfaces import (
    IFolder,
    SERVICES_NAME
    )

@colander.deferred
def name_validator(node, kw):
    context = kw['request'].context
    def namecheck(node, value):
        try:
            context.check_name(value)
        except Exception as e:
            raise colander.Invalid(node, e.message, value)
        
    return colander.All(
        colander.Length(min=1, max=100),
        namecheck,
        )

class AddFolderSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator=name_validator,
        )

@mgmt_view(context=IFolder, name='add_folder', tab_condition=False,
           permission='add content', 
           renderer='substanced.sdi:templates/form.pt')
class AddFolderView(FormView):
    title = 'Add Folder'
    schema = AddFolderSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct['name']
        folder = registry.content.create(IFolder)
        self.request.context[name] = folder
        return HTTPFound(location=self.request.mgmt_path(folder, '@@contents'))

# TODO: rename, cut, copy, paste

@mgmt_view(context=IFolder, name='contents', 
           renderer='substanced.sdi:templates/contents.pt',
           permission='view')
def folder_contents(context, request):
    can_manage = has_permission('manage contents', context, request)
    L = []
    for k, v in context.items():
        viewable = False
        url = request.mgmt_path(v)
        if has_permission('view', v, request):
            viewable = True
        icon = request.registry.content.metadata(v, 'icon')
        deletable = can_manage and k != SERVICES_NAME
        data = dict(name=k, deletable=deletable, viewable=viewable, url=url, 
                    icon=icon)
        L.append(data)
    batchinfo = get_batchinfo(L, request, url=request.url)
    return dict(batchinfo=batchinfo)

@mgmt_view(context=IFolder, name='delete_folder_contents',request_method='POST',
           permission='manage contents', tab_condition=False, check_csrf=True)
def delete_folder_contents(context, request):
    todelete = request.POST.getall('delete')
    deleted = 0
    for name in todelete:
        v = context.get(name)
        if v is not None:
            del context[name]
            deleted += 1
    if not deleted:
        msg = 'No items deleted'
        request.session.flash(msg)
    elif deleted == 1:
        msg = 'Deleted 1 item'
        request.flash_undo(msg)
    else:
        msg = 'Deleted %s items' % deleted
        request.flash_undo(msg)
    return HTTPFound(request.mgmt_path(context, '@@contents'))

