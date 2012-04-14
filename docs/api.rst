.. _substanced_api:

:mod:`substanced` API
---------------------------

.. automodule:: substanced

.. autofunction:: includeme

:mod:`substanced.catalog` API
-----------------------------

.. automodule:: substanced.catalog

.. autoclass:: Catalog
   :members:
   :inherited-members:

   .. automethod:: __setitem__

   .. automethod:: __getitem__

   Retrieve an index.

   .. automethod:: get

   Retrieve an index or return failobj.

.. autofunction:: includeme

XXX: request.search, request.query

:mod:`substanced.catalog.discriminators` API
--------------------------------------------

.. automodule:: substanced.catalog.discriminators

.. autofunction:: get_title

.. autofunction:: get_interfaces

.. autofunction:: get_containment

.. autofunction:: get_textrepr

.. autofunction:: get_creation_date

.. autofunction:: get_modified_date

.. autofunction:: get_allowed_to_view

:mod:`repoze.catalog.query` API
-------------------------------

.. module:: repoze.catalog.query

Comparators
~~~~~~~~~~~

.. autoclass:: Contains

.. autoclass:: Eq

.. autoclass:: NotEq

.. autoclass:: Gt

.. autoclass:: Lt

.. autoclass:: Ge

.. autoclass:: Le

.. autoclass:: Contains

.. autoclass:: DoesNotContain

.. autoclass:: Any

.. autoclass:: NotAny

.. autoclass:: All

.. autoclass:: NotAll

.. autoclass:: InRange

.. autoclass:: NotInRange

Boolean Operators
~~~~~~~~~~~~~~~~~

.. autoclass:: Or

.. autoclass:: And

.. autoclass:: Not

Other Helpers
~~~~~~~~~~~~~

.. autoclass:: Name

.. autofunction:: parse_query

:mod:`substanced.catalog.indexes` API
-------------------------------------

.. automodule:: substanced.catalog.indexes

.. autoclass:: FieldIndex
   :members:

.. autoclass:: KeywordIndex
   :members:

.. autoclass:: TextIndex
   :members:

.. autoclass:: FacetIndex
   :members:

.. autoclass:: PathIndex
   :members:

:mod:`substanced.catalog.subscribers` API
-----------------------------------------

.. automodule:: substanced.catalog.subscribers

.. autofunction:: object_added

.. autofunction:: object_will_be_removed

.. autofunction:: object_modified

:mod:`substanced.objectmap` API
--------------------------------

.. automodule:: substanced.objectmap

.. autoclass:: ObjectMap
   :members:

.. autofunction:: includeme


