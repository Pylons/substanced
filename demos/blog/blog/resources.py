import datetime
import time

from persistent import Persistent
from pytz import timezone

from pyramid.security import (
    Allow,
    Everyone,
    )

from colander import (
    DateTime,
    deferred,
    Invalid,
    OneOf,
    SchemaNode,
    String,
    )

from deform.widget import (
    SelectWidget,
    TextAreaWidget,
    )

from substanced.content import content
from substanced.schema import Schema
from substanced.folder import Folder
from substanced.property import PropertySheet
from substanced.root import (
    Root,
    RootPropertySheet,
    )

def make_name_validator(content_type):
    @deferred
    def name_validator(node, kw):
        request = kw['request']
        context = request.context
        def exists(node, value):
            if request.registry.content.istype(context, content_type):
                if value != context.__name__:
                    try:
                        context.__parent__.check_name(value)
                    except Exception as e:
                        raise Invalid(node, e.args[0], value)
            else:
                try:
                    context.check_name(value)
                except Exception as e:
                    raise Invalid(node, e.args[0], value)

        return exists
    return name_validator

@deferred
def now_default(node, kw):
    return datetime.date.today()

eastern = timezone('America/New_York')

class BlogEntrySchema(Schema):
    name = SchemaNode(
        String(),
        validator = make_name_validator('Blog Entry'),
        )
    title = SchemaNode(
        String(),
        )
    entry = SchemaNode(
        String(),
        widget = TextAreaWidget(rows=20, cols=70),
        )
    format = SchemaNode(
        String(),
        validator = OneOf(['rst', 'html']),
        widget = SelectWidget(
            values=[('rst', 'rst'), ('html', 'html')]),
        )
    pubdate = SchemaNode(
       DateTime(default_tzinfo=eastern),
       default = now_default,
       )

class BlogEntryPropertySheet(PropertySheet):
    schema = BlogEntrySchema()
    def get(self):
        context = self.context
        return dict(title=context.title,
                    entry=context.entry,
                    format=context.format,
                    pubdate=context.pubdate,
                    name=context.__name__)

    def set(self, struct):
        context = self.context
        if struct['name'] != context.__name__:
            context.__parent__.rename(context.__name__, struct['name'])
        context.title = struct['title']
        context.entry = struct['entry']
        context.format = struct['format']
        context.pubdate = struct['pubdate']

@content(
    'Blog Entry',
    icon='icon-book',
    add_view='add_blog_entry',
    propertysheets=(
        ('Basic', BlogEntryPropertySheet),
        ),
    catalog=True,
    tab_order=('properties', 'contents', 'acl_edit'),
    )
class BlogEntry(Folder):
    def __init__(self, title, entry, format, pubdate):
        Folder.__init__(self)
        self.modified = datetime.datetime.now()
        self.title = title
        self.entry = entry
        self.pubdate = pubdate
        self.format = format
        self['attachments'] = Folder()
        self['comments'] = Folder()

    def add_comment(self, comment):
        while 1:
            name = str(time.time())
            if not name in self:
                self['comments'][name] = comment
                break

class CommentSchema(Schema):
    commenter = SchemaNode(
       String(),
       )
    text = SchemaNode(
       String(),
       )
    pubdate = SchemaNode(
       DateTime(),
       default = now_default,
       )

class CommentPropertySheet(PropertySheet):
    schema = CommentSchema()

@content(
    'Comment',
    icon='icon-comment',
    add_view='add_comment',
    propertysheets = (
        ('Basic', CommentPropertySheet),
        ),
    catalog = True,
    )
class Comment(Persistent):
    def __init__(self, commenter_name, text, pubdate):
        self.commenter_name = commenter_name
        self.text = text
        self.pubdate = pubdate

@content(
    'Root',
    icon='icon-home',
    propertysheets = (
        ('Basic', RootPropertySheet),
        ),
    )
def Blog(*arg, **kw):
    root = Root(*arg, **kw)
    acl = getattr(root, '__acl__', [])
    acl.append((Allow, Everyone, 'view'))
    root.__acl__ = acl
    return root

