Defining Content
================

A content constructor must have these properties:

- It must be a class, or a factory function that returns an instance of a
  class.

- Instances of the class must be *persistent* (it must derive from the
  ``persistent.Persistent`` class or a class that derives from it such as
  ``substanced.folder.Folder``).

- The class or factory must be decorated with the ``@content`` decorator, or
  must be added imperatively at configuration time via
  ``config.add_content_type``.

- It must have a *type*.  A type acts as a categorization marker, and allows
  the content to be constructed and enumerated by various Substance D APIs.
  The type is defined as a class that inherits from the
  ``substanced.content.Type`` class.

Using content is a nice way to let you populate the management UI with
choices.  For example, if you register several types in a given category, you
can easily get a listing of them to put into a dropdown of constructable
items on an "add form".

Here's an example which defines a content constructor as a class:

.. code-block:: python

   # in a module named blog.models

   from persistent import Persistent
   from substanced.content import (
       Type,
       content,
       )     

   class BlogEntryType(Type):
       pass

   @content(BlogEntryType)
   class BlogEntry(Persistent):
       def __init__(self, title, body):
           self.title = title
           self.body = body

Here's an example of defining a content type factory using a function
instead:

.. code-block:: python

   # in a module named blog.models

   from persistent import Persistent
   from substanced.content import (
       Type,
       content,
       )     

   class BlogEntryType(Type):
       pass

   class BlogEntry(Persistent):
       def __init__(self, title, body):
           self.title = title
           self.body = body

   @content(BlogEntryType)
   def make_blog_entry(title, body):
       return BlogEntry(title, body)

In order to activate a ``@content`` decorator, it must be *scanned* using the
Pyramid ``config.scan()`` machinery:

.. code-block:: python

   # in a module named blog.__init__

   from pyramid.config import Configurator

   def main(global_config, **settings):
       config = Configurator()
       config.scan('blog.models')

Instead of using the ``@content`` decorator, you can also add a content type
imperatively at configuration time using the ``add_content_type`` method of
the Configurator:

.. code-block:: python

   # in a module named blog.__init__

   from pyramid.config import Configurator
   from .models import BlogEntryType, BlogEntry

   def main(global_config, **settings):
       config = Configurator()
       config.include('substanced')
       config.add_content_type(BlogEntryType, BlogEntry)

You don't need to scan your module if you use ``add_content_type`` rather
than the ``@content`` decorator.

Once a content type has been defined (and scanned, if it's been defined using
a decorator), an instance of the type can be constructed from within a view
that lives in your application:

.. code-block:: python

   # in a module named blog.views

   from pyramid.httpexceptions import HTTPFound
   from .models import BlogEntryType

   @view_config(name='add_blog_entry', request_method='POST')
   def add_blogentry(request):
       title = request.POST['title']
       body = request.POST['body']
       entry = request.content.create(BlogEntryType, title, body)
       context['title] = entry
       return HTTPFound(request.resource_url(entry))

The arguments passed to ``request.content.create`` must start with the
content type class, and must be followed with whatever arguments are required
by the content constructor.

Creating an instance of content this way isn't particularly more useful than
creating an instance of the content object directly by calling its class.
But if you use types, they can also be enumerated:

.. code-block:: python

   # in a module named blog.views

   @view_config(name='show_types', renderer='show_types.pt')
   def show_types(request):
       all_types = request.content.all()
       return {'all_types':all_types}

``request.content.all()`` will return all type objects you've defined and
scanned.

You can categorize types into particular "buckets" by passing a *second* type
to the ``@content`` decorator:

.. code-block:: python

   # in a module named blog.models

   from persistent import Persistent
   from substanced.content import (
       Type,
       content,
       )     

   class BlogType(Type):
       pass

   class BlogEntryType(Type):
       pass

   class BlogPictureType(Type):
       pass

   @content(BlogEntryType, BlogType)
   class BlogEntry(Persistent):
       def __init__(self, title, body):
           self.title = title
           self.body = body

   @content(BlogPictureType, BlogType)
   class BlogPicture(Persistent):
       def __init__(self, title, data):
           self.title = title
           self.data = data

In the above example, ``BlogPictureType`` is the content type, and
``BlogType`` is the categorization type.

Once you've categorized content like this, you can make use of the categories
in the ``create`` and ``all`` APIs:

.. code-block:: python

   # in a module named blog.views

   from pyramid.httpexceptions import HTTPFound
   from .models import BlogType, BlogEntryType

   @view_config(name='add_blog_entry', request_method='POST')
   def add_blogentry(request):
       title = request.POST['title']
       body = request.POST['body']
       entry = request.content[BlogType].create(BlogEntryType, title, body)
       context['title] = entry
       return HTTPFound(request.resource_url(entry))

.. code-block:: python

   # in a module named blog.views

   from .models import BlogType

   @view_config(name='show_blog_types', renderer='show_types.pt')
   def show_types(request):
       blog_types = request.content[BlogType].all()
       return {'blog_types':blog_types}

You can check if a piece of content is of a particular category by using
``request.content[category_type].provided_by``:

.. code-block:: python

   # in a module named blog.views

   from .models import BlogType

   @view_config(name='check_type', renderer='string')
   def check(request):
       if request.content[BlogType].provided_by(request.context):
           return "It's a blog type (a blog entry or a picture)"
       return "It's not a blog type"
