Defining Content
================

:term:`Resource` is the term that Substance D uses to describe an object
placed in the :term:`resource tree`.  

Ideally, all resources in your resource tree will be :term:`content`. "Content"
is the term that Substance D uses to describe resource objects that are
particularly well-behaved when they appear in the SDI management interface.
The Substance D management interface (aka :term:`SDI`) is a set of views
imposed upon the resource tree that allow you to add, delete, change and
otherwise manage resources.

You can convince the management interface that your particular resources are
content.  To define a resource as content, you need to associate a resource
with a :term:`content type`.

Registering Content
-------------------

In order to add new content to the system, you need to associate a
:term:`resource factory` with a :term:`content type`.  A resource factory that
generates content must have these properties:

- It must be a class, or a factory function that returns an instance of a
  resource class.

- Instances of the resource class must be *persistent* (it must derive from
  the ``persistent.Persistent`` class or a class that derives from Persistent
  such as :class:`substanced.folder.Folder`).

- The resource class or factory must be decorated with the ``@content``
  decorator, or must be added at configuration time via
  ``config.add_content_type``.

- It must have a *type*.  A type acts as a globally unique categorization
  marker, and allows the content to be constructed, enumerated, and
  introspected by various Substance D UI elements such as "add forms", and
  queries by the management interface for the icon name of a resource.  A
  type can be any hashable Python object, but it's most often a string.

Here's an example which defines a content resource factory as a class:

.. code-block:: python

   # in a module named blog.resources

   from persistent import Persistent
   from substanced.content import content

   @content('Blog Entry')
   class BlogEntry(Persistent):
       def __init__(self, title, body):
           self.title = title
           self.body = body

Here's an example of defining a content resource factory using a function
instead:

.. code-block:: python

   # in a module named blog.resources

   from persistent import Persistent
   from substanced.content import content

   class BlogEntry(Persistent):
       def __init__(self, title, body):
           self.title = title
           self.body = body

   @content('Blog Entry')
   def make_blog_entry(title, body):
       return BlogEntry(title, body)

.. note::

   When a resource factory is not a class, Substance D will wrap the resource
   factory in something that changes the resource object returned from the
   factory.  In the above case, the BlogEntry instance returned from
   ``make_blog_entry`` will be changed; its ``__factory_type__`` attribute
   will be mutated.

In order to activate a ``@content`` decorator, it must be *scanned* using the
Pyramid ``config.scan()`` machinery:

.. code-block:: python

   # in a module named blog.__init__

   from pyramid.config import Configurator

   def main(global_config, **settings):
       config = Configurator()
       config.include('substanced')
       config.scan('blog.resources')
       # .. and so on ...

Instead of using the ``@content`` decorator, you can alternately add a
content resource imperatively at configuration time using the
``add_content_type`` method of the Configurator:

.. code-block:: python

   # in a module named blog.__init__

   from pyramid.config import Configurator
   from .resources import BlogEntry

   def main(global_config, **settings):
       config = Configurator()
       config.include('substanced')
       config.add_content_type('Blog Entry', BlogEntry)

This does the same thing as using the ``@content`` decorator, but you don't
need to ``scan()`` your resources if you use ``add_content_type`` instead of
the ``@content`` decorator.

Once a content type has been defined (and scanned, if it's been defined using
a decorator), an instance of the resource can be constructed from within a
view that lives in your application:

.. code-block:: python

   # in a module named blog.views

   from pyramid.httpexceptions import HTTPFound

   @view_config(name='add_blog_entry', request_method='POST')
   def add_blogentry(request):
       title = request.POST['title']
       body = request.POST['body']
       entry = request.registry.content.create('Blog Entry', title, body)
       context['title] = entry
       return HTTPFound(request.resource_url(entry))

The arguments passed to ``request.registry.content.create`` must start with
the content type, and must be followed with whatever arguments are required
by the resource factory.

Creating an instance of content this way isn't particularly more useful than
creating an instance of the resource object by calling its class ``__init__``
directly unless you're building a highly abstract system.  But even if you're
not building a very abstract system, types can be very useful.  For instance,
types can be enumerated:

.. code-block:: python

   # in a module named blog.views

   @view_config(name='show_types', renderer='show_types.pt')
   def show_types(request):
       all_types = request.registry.content.all()
       return {'all_types':all_types}

``request.registry.content.all()`` will return all the types you've defined
and scanned.

Metadata
--------

A content's type can be associated with metadata about that type, including the
content type's name, its icon in the SDI management interface, an add view
name, and other things.  Pass arbitrary keyword arguments to the ``@content``
decorator or ``config.add_content_type`` to specify metadata.

Names
~~~~~

You can associate a content type registration with a name that shows up when
someone attempts to add such a piece of content using the SDI management
interface "Add" tab by passing a ``name`` keyword argument to ``@content``
or ``config.add_content_type``.

.. code-block:: python

   # in a module named blog.resources

   from persistent import Persistent
   from substanced.content import content

   @content('Blog Entry', name='Cool Blog Entry')
   class BlogEntry(Persistent):
       def __init__(self, title, body):
           self.title = title
           self.body = body

Once you've done this, the "Add" tab in the SDI management interface will
show your content as addable using this name instead of the type name.

Icons
~~~~~

You can associate a content type registration with a management view icon by
passing an ``icon`` keyword argument to ``@content`` or ``add_content_type``.

.. code-block:: python

   # in a module named blog.resources

   from persistent import Persistent
   from substanced.content import content

   @content('Blog Entry', icon='icon-file')
   class BlogEntry(Persistent):
       def __init__(self, title, body):
           self.title = title
           self.body = body

Once you've done this, content you add to a folder in the sytem will display
the icon next to it in the contents view of the management interface and in
the breadcrumb list.  The available icon names are listed at
http://twitter.github.com/bootstrap/base-css.html#icons .

You can also pass a callback as an ``icon`` argument:

.. code-block:: python

   from persistent import Persistent
   from substanced.content import content

   def blogentry_icon(context, request):
       if context.body:
           return 'icon-file'
       else:
           return 'icon-gift'

   @content('Blog Entry', icon=blogentry_icon)
   class BlogEntry(Persistent):
       def __init__(self, title, body):
           self.title = title
           self.body = body

A callable used as ``icon`` must accept two arguments: ``context`` and
``request``.  ``context`` will be an instance of the type and ``request`` will
be the current request; your callback will be called at the time the folder
view is drawn.  The callable should return either an icon name or ``None``.
For example, the above ``blogentry_icon`` callable tells the SDI to use an icon
representing a file if the blogentry has a body, otherwise show an icon
representing gift.

Add Views
~~~~~~~~~

You can associate a content type with a view that will allow the type to be
added by passing the name of the add view as a keyword argument to
``@content`` or ``add_content_type``.

.. code-block:: python

   # in a module named blog.resources

   from persistent import Persistent
   from substanced.content import content

   @content('Blog Entry', add_view='add_blog_entry')
   class BlogEntry(Persistent):
       def __init__(self, title, body):
           self.title = title
           self.body = body

Once you've done this, if the button is clicked in the "Add" tab for this
content type, the related view will be presented to the user.

You can also pass a callback as an ``add_view`` argument:

.. code-block:: python

   from persistent import Persistent
   from substanced.content import content
   from substanced.folder import Folder

   def add_blog_entry(context, request):
       if request.registry.content.istype(context, 'Blog'):
           return 'add_blog_entry'

   @content('Blog')
   class Blog(Folder):
       pass

   @content('Blog Entry', add_view=add_blog_entry)
   class BlogEntry(Persistent):
       def __init__(self, title, body):
           self.title = title
           self.body = body

A callable used as ``add_view`` must accept two arguments: ``context`` and
``request``.  ``context`` will be the potential parent object of the content
(when the SDI folder view is drawn), and ``request`` will be the current
request at the time the folder view is drawn.  The callable should return
either a view name or ``None`` if the content should not be addable in this
circumstance.  For example, the above ``add_blog_entry`` callable asserts that
Blog Entry content should only be addable if the context we're adding to is of
type Blog; it returns None otherwise, signifying that the content is not
addable in this circumstance.

Obtaining Metadata About a Content Object's Type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``request.registry.content.metadata(blogentry, 'icon')``

  Will return the icon for the blogentry's content type or ``None`` if it
  does not exist.

``request.registry.content.metadata(blogentry, 'icon', 'icon-file')``

  Will return the icon for the blogentry's content type or ``icon-file`` if
  it does not exist.
