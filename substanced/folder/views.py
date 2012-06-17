import colander

from pyramid.httpexceptions import HTTPFound
from pyramid.security import has_permission

from ..schema import Schema
from ..form import FormView
from ..sdi import (
    mgmt_view,
    get_add_views,
    )
from ..util import Batch

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
            raise colander.Invalid(node, e.args[0], value)

    return colander.All(
        colander.Length(min=1, max=100),
        namecheck,
        )

class AddFolderSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator=name_validator,
        )

@mgmt_view(context=IFolder,
           name='add_folder',
           tab_condition=False,
           permission='sdi.add-content',
           renderer='substanced.sdi:templates/form.pt')
class AddFolderView(FormView):
    title = 'Add Folder'
    schema = AddFolderSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct['name']
        folder = registry.content.create(IFolder)
        self.context[name] = folder
        return HTTPFound(location=self.request.mgmt_path(folder, '@@contents'))

# TODO: rename, cut, copy, paste

class FolderContentsViews(object):

    get_add_views = staticmethod(get_add_views) # for testing

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @mgmt_view(context=IFolder,
               name='contents', 
               renderer='templates/contents.pt',
               permission='sdi.view')
    def show(self):
        context = self.context
        request = self.request
        can_manage = has_permission('sdi.manage-contents', context, request)
        L = []
        for k, v in context.items():
            viewable = False
            url = request.mgmt_path(v, '@@manage_main')
            if has_permission('sdi.view', v, request):
                viewable = True
            icon = request.registry.content.metadata(v, 'icon')
            deletable = can_manage and k != SERVICES_NAME
            data = dict(name=k, deletable=deletable, viewable=viewable,
                        url=url, icon=icon)
            L.append(data)
        addables = self.get_add_views(request, context)
        batch = Batch(L, request)
        return dict(batch=batch, addables=addables)

    @mgmt_view(context=IFolder,
               name='delete_folder_contents',
               request_method='POST',
               permission='sdi.manage-contents',
               tab_condition=False, 
               check_csrf=True)
    def delete(self):
        request = self.request
        context = self.context
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
            request.flash_with_undo(msg)
        else:
            msg = 'Deleted %s items' % deleted
            request.flash_with_undo(msg)
        return HTTPFound(request.mgmt_path(context, '@@contents'))

