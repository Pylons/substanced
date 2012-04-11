from persistent import Persistent

from pyramid.httpexceptions import HTTPFound

import colander
import deform.widget

from substanced.interfaces import (
    IFolder,
    IPropertied
    )
from substanced.schema import Schema
from substanced.content import content
from substanced.sdi import mgmt_view
from substanced.form import FormView

class DocumentSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        )
    title = colander.SchemaNode(
        colander.String(),
        )
    body = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.RichTextWidget()
        )

class DocumentType(IPropertied):
    pass

@content(DocumentType, icon='icon-file')
class Document(Persistent):
    __propschema__ = DocumentSchema()
    def __init__(self, title, body):
        self.title = title
        self.body = body
        
    def get_properties(self):
        return dict(name=self.__name__, description=self.description,
                    title=self.title)

    def set_properties(self, struct):
        newname = struct['name']
        oldname = self.__name__
        if newname != oldname:
            parent = self.__parent__
            parent.rename(oldname, newname)
        self.description = struct['description']
        self.title = struct['title']
    
@mgmt_view(context=IFolder, name='add document', tab_title='Add Document', 
           permission='add content', 
           renderer='substanced.sdi:templates/form.pt')
class AddUserView(FormView):
    title = 'Add User'
    schema = DocumentSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('name')
        document = registry.content.create(DocumentType, **appstruct)
        self.request.context[name] = document
        return HTTPFound(self.request.mgmt_path(document, '@@properties'))
    
