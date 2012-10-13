Management Views
-----------------

A :term:`management view` is a :term:`view configuration` that applies only
when the URL is prepended with the :term:`manage prefix`. The manage prefix
is usually ``/manage``, unless you've changed it from its default by setting
a custom ``substanced.manage_prefix`` in your application's ``.ini`` file.

This means that views declared as management views will never show up in your
application's "retail" interface (the interface that normal unprivileged
users see).  They'll only show up when a user is using the :term:`SDI` to
manage content.

There are two ways to define management views:

- Using the :class:`substanced.sdi.mgmt_view` decorator on a function,
  method, or class.

- Using the :func:`substanced.sdi.add_mgmt_view` Configurator (aka.
  ``config.add_mgmt_view``) API.

The former is most convenient, but they are functionally equivalent.
``mgmt_view`` just calls into ``add_mgmt_view`` when found via a
:term:`scan`.

Declaring a management view is much the same as declaring a "normal" Pyramid
view using :class:`pyramid.view.view_config` with a ``route_name`` of
``substanced_manage``.  For example, each of the following view declarations
will register a view that will show up when the ``/manage/foobar`` URL is
visited:

.. code-block:: python
   :linenos:

   from pyramid.view import view_config

   @view_config(
       renderer='string',
       route_name='substanced_manage', 
       name='foobar'
       )
   def foobar(request):
       return 'Foobar!'

The above is largely functionally the same as this:

.. code-block:: python
   :linenos:

   from substanced.sdi import mgmt_view

   @mgmt_view(renderer='string', name='foobar')
   def foobar(request):
       return 'Foobar!'

Management views, in other words, are really just plain-old Pyramid views
with a slightly shorter syntax for definition.  Declaring a view a management
view, however, does do some extra things that make it advisable to use rather
than a plain Pyramid view registration:

- It registers *introspectable* objects that the SDI interface uses to try to
  find management interface tabs (the row of actions at the top of every
  management view rendering).

- It allows you to associate a tab title, a tab condition, and cross-site
  request forgery attributes with the view.

So if you want things to work right when developing management views, you'll
use ``@mgmt_view`` instead of ``@view_config``, and ``config.add_mgmt_view``
instead of ``config.add_view``.
