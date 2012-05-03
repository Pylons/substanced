from webob.exc import HTTPFound
from substanced.sdi import mgmt_view
from substanced.form import FormView
from substanced.interfaces import ISite

from ..resources import (
    IBlogEntry,
    BlogEntrySchema,
    )

@mgmt_view(
    context=ISite,
    name='add_blog_entry',
    permission='sdi.add-content', 
    renderer='substanced.sdi:templates/form.pt',
    tab_condition=False,
    )
class AddBlogEntryView(FormView):
    title = 'Add Blog Entry'
    schema = BlogEntrySchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        name = appstruct.pop('name')
        request = self.request
        blogentry = request.registry.content.create(IBlogEntry, **appstruct)
        self.context[name] = blogentry
        loc = request.mgmt_path(self.context, name, '@@properties')
        return HTTPFound(location=loc)

