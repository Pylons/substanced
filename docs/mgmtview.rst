================
Management Views
================

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

Tab Ordering
============

If you register a management view, a tab will be added in the list of
tabs. By default, the tab order will use a default sorting: alphabetical
order by the ``tab_title`` parameter of each tab (or the view name if no
``tab_title`` is provided.) The first tab in this tab listing acts as
the "default" that is open when you visit a resource. Substance D does,
though, give you some options to control tab ordering in larger systems
with different software registering management views.

Perhaps, though, a developer wants to ensure that one of her tabs
appears first in the list and another appears last,
no matter what other management views have been registered by Substance
D or any add-on packages. ``@mgmt_view`` (or the imperative call) allow
a keyword of ``tab_before`` or ``tab_after``. Each take a value of
either:

- The string tab ``name`` of the management view to place before or
  after.

- A ``FIRST``, ``LAST``, or ``MIDDLE`` "sentinel" imported from
  ``pyramid.util``

As in many cases, an illustration is helpful:

.. code-block:: python

    from substanced.sdi import FIRST, MIDDLE

    @mgmt_view(name='tab_1', tab_title='Tab 1',
               renderer='templates/tab_1.pt'
    )
    def tab_1(context, request):
        return {}


    @mgmt_view(name='tab_2', tab_title='Tab 2',
               renderer='templates/tab_1.pt',
               tab_before='tab_1')
    def tab_2(context, request):
        return {}


    @mgmt_view(name='tab_3', tab_title='Tab 3',
               renderer='templates/tab_1.pt', tab_after=FIRST)
    def tab_3(context, request):
        return {}


    @mgmt_view(name='tab_4', tab_title='Tab 4',
               renderer='templates/tab_1.pt', tab_after=MIDDLE)
    def tab_4(context, request):
        return {}


    @mgmt_view(name='tab_5', tab_title='Tab 5',
               renderer='templates/tab_1.pt')
    def tab_5(context, request):
        return {}

This set of management views (combined with the built-in Substance D
management views for ``Contents`` and ``Security``) results in::

  Tab 3 | Contents | Security | Tab 2 | Tab 1 | Tab 5 | Tab 4

These management view arguments apply to any content type that the view
is registered for. What if you want to allow a content type to
influence the tab ordering? As mentioned in the
:doc:`content type docs <content>`, the ``tab_order`` parameter
overrides the mgmt_view tab settings, for a content type, with a
sequence of view names that should be ordered (and everything
not in the sequence, after.)

Filling Slots
=============

Each management view that you write plugs into various parts of the SDI
UI.

- title, content, flash messages, head, tail