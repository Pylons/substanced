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

@colander.deferred
def name_validator(node, kw):
    context = kw['request'].context
    def exists(node, value):
        if DocumentType.providedBy(context):
            if value != context.__name__:
                try:
                    context.__parent__.check_name(value)
                except Exception as e:
                    raise colander.Invalid(node, e.message, value)
        else:
            try:
                context.check_name(value)
            except Exception as e:
                raise colander.Invalid(node, e.message, value)
                
    return exists

class DocumentSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator = name_validator,
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

@content(DocumentType, icon='icon-file', add_view='add_document', 
         name='Document')
class Document(Persistent):

    __propschema__ = DocumentSchema()

    def __init__(self, title, body):
        self.title = title
        self.body = body
        
    def get_properties(self):
        return dict(name=self.__name__, body=self.body, title=self.title)

    def set_properties(self, struct):
        newname = struct['name']
        oldname = self.__name__
        if newname != oldname:
            parent = self.__parent__
            parent.rename(oldname, newname)
        self.body = struct['body']
        self.title = struct['title']

    
@mgmt_view(context=IFolder, name='add_document', tab_title='Add Document', 
           permission='add content', 
           renderer='substanced.sdi:templates/form.pt', tab_condition=False)
class AddDocumentView(FormView):
    title = 'Add Document'
    schema = DocumentSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('name')
        document = registry.content.create(DocumentType, **appstruct)
        self.request.context[name] = document
        return HTTPFound(self.request.mgmt_path(document, '@@properties'))

