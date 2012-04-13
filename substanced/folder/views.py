import colander

from pyramid.httpexceptions import HTTPFound

from ..schema import Schema
from ..form import FormView
from ..interfaces import IFolder
from ..sdi import mgmt_view

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

