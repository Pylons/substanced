=========
API Views
=========

Substance D provides a set of API views for creating, reading, updating
and deleting :term:`content` resources represented as JSON.

An :term:`API view` is a :term:`view configuration` that applies only
when the URL is prepended with the :term:`API prefix`. The API prefix
is usually ``/api``, unless you've changed it from its default by setting
a custom ``substanced.api_prefix`` in your application's ``.ini`` file.

This means that views declared as API views will never show up in your
application's "retail" interface (the interface that normal unprivileged
users see).  They'll only show up when a user intentionally accesses an
API-prefixed URL, whether via a browser or via an HTTP client library such
as `requests <http://docs.python-requests.org/en/latest/>`_.

Standard API Views
==================


Defining Custom API Views
=========================

There are two ways to define API views:

- Using the :class:`substanced.api.api_view` decorator on a function,
  method, or class.

- Using the :func:`substanced.api.add_api_view` Configurator (aka.
  ``config.add_api_view``) API.

The former is most convenient, but they are functionally equivalent.
``api_view`` just calls into ``add_api_view`` when found via a
:term:`scan`.

For example, the following view declaration registers a view
that will show up when the ``/api/foobar`` URL is visited:

.. code-block:: python
   :linenos:

   from substanced.api import api_view

   @api_view(name='foobar')
   def foobar(request):
       return 42

Defining an API view is much the same as defining a normal Pyramid view,
but differs in the following ways:

* The `route_name` defaults to ``substanced_api`` so that the view will
  only be available under the :term:`API prefix`.

* The `renderer` defaults to ``json`` (the JSON renderer).

* The `permission` defaults to ``api.view``.


``api_view`` View Predicates
=============================

Since ``api_view`` is an extension of Pyramid's ``view_config``,
it re-uses the same concept of view predicates as well as some of the
same actual predicates:

- ``request_type``, ``request_method``, ``request_param``,
  ``containment``, ``attr``, ``renderer``, ``wrapper``, ``xhr``,
  ``accept``, ``header``, ``path_info``, ``context``, ``name``,
  ``custom_predicates``, ``decorator``, ``mapper``, and ``http_cache``
  are supported and behave the same.

- ``permission`` is the same but defaults to ``api.view``.
