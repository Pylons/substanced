.. _substanced_api:

:mod:`substanced` API
---------------------------

.. automodule:: substanced

.. autofunction:: includeme

.. autofunction:: root_factory

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

XXX: request.search_catalog, request.query_catalog

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

:mod:`hypatia.query` API
-------------------------------

.. module:: hypatia.query

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

:mod:`substanced.content` API
-----------------------------

.. automodule:: substanced.content

.. autofunction:: get_content_type

.. autofunction:: find_content

.. autofunction:: find_service

.. autofunction:: find_services

.. autoclass:: content
   :members:

.. autoclass:: service
   :members:

.. autofunction:: add_content_type

.. autofunction:: add_service_type

.. autoclass:: ContentRegistry
   :members:

.. autofunction:: includeme

:mod:`substanced.event` API
---------------------------

.. automodule:: substanced.event

.. autoclass:: ObjectAdded
   :members:
   :inherited-members:

.. autoclass:: ObjectWillBeAdded
   :members:
   :inherited-members:

.. autoclass:: ObjectRemoved
   :members:
   :inherited-members:

.. autoclass:: ObjectWillBeRemoved
   :members:
   :inherited-members:

.. autoclass:: ObjectModified
   :members:
   :inherited-members:

.. autoclass:: subscribe_added
   :members:
   :inherited-members:

.. autoclass:: subscribe_removed
   :members:
   :inherited-members:

.. autoclass:: subscribe_will_be_added
   :members:
   :inherited-members:

.. autoclass:: subscribe_will_be_removed
   :members:
   :inherited-members:

.. autoclass:: subscribe_modified
   :members:
   :inherited-members:

:mod:`substanced.evolution` API
--------------------------------

.. automodule:: substanced.evolution

.. autofunction:: add_evolution_package

.. autofunction:: includeme

:mod:`substanced.file` API
-----------------------------

.. automodule:: substanced.file

.. attribute:: USE_MAGIC

   A constant value used as an argument to various methods of the
   :class:`substanced.file.File` class.

.. autoclass:: File
   :members:

   .. automethod:: __init__

   .. attribute:: blob

      The ZODB blob object associated with this file.

   .. attribute:: mimetype
 
      The mimetype of this file object (a string).

.. autofunction:: includeme

:mod:`substanced.folder` API
----------------------------

.. automodule:: substanced.folder

.. autoclass:: Folder
   :members:

   .. automethod:: __init__

   .. attribute:: order

     A tuple of name values. If set, controls the order in which names should
     be returned from ``__iter__()``, ``keys()``, ``values()``, and
     ``items()``.  If not set, use an effectively random order.

.. autoclass:: SequentialAutoNamingFolder

   .. automethod:: __init__

   .. automethod:: add_autoname

   .. automethod:: next_name

   .. automethod:: add

.. autoclass:: RandomAutoNamingFolder

   .. automethod:: __init__

   .. automethod:: add_autoname

   .. automethod:: next_name

.. autofunction:: includeme

:mod:`substanced.form` API
----------------------------

.. automodule:: substanced.form

.. autoclass:: Form
   :members:

.. autoclass:: FormView
   :members:

.. autoclass:: FileUploadTempStore
   :members:


:mod:`substanced.objectmap` API
--------------------------------

.. automodule:: substanced.objectmap

.. autofunction:: find_objectmap

.. autoclass:: ObjectMap
   :members:

.. autoclass:: Multireference
   :members:

.. autofunction:: reference_sourceid_property

.. autofunction:: reference_source_property

.. autofunction:: reference_targetid_property

.. autofunction:: reference_target_property

.. autofunction:: multireference_sourceid_property

.. autofunction:: multireference_source_property

.. autofunction:: multireference_targetid_property

.. autofunction:: multireference_target_property

.. autofunction:: includeme


:mod:`substanced.principal` API
--------------------------------

.. automodule:: substanced.principal

.. autoclass:: UserToGroup
   :members:

.. autoclass:: Principals
   :members:

.. autoclass:: Users
   :members:

.. autoclass:: Groups
   :members:

.. autoclass:: GroupSchema
   :members:

.. autoclass:: Group
   :members:

.. autoclass:: UserSchema
   :members:

.. autoclass:: User
   :members:

.. autofunction:: groupfinder

.. autofunction:: includeme

:mod:`substanced.property` API
--------------------------------

.. automodule:: substanced.property

.. autoclass:: PropertySheet

:mod:`substanced.schema` API
----------------------------

.. automodule:: substanced.schema

.. autoclass:: Schema
   :members:

:mod:`substanced.sdi` API
----------------------------

.. automodule:: substanced.sdi

.. autofunction:: add_mgmt_view

.. autofunction:: check_csrf_token

.. autoclass:: mgmt_view

:mod:`substanced.root` API
--------------------------

.. automodule:: substanced.root

.. autoclass:: Root
   :members:

.. autofunction:: includeme

:mod:`substanced.util` API
--------------------------

.. automodule:: substanced.util

.. autofunction:: coarse_datetime_repr

.. autofunction:: postorder

.. autofunction:: oid_of

.. autoclass:: Batch

.. autofunction:: merge_url_qs

.. autofunction:: chunks

:mod:`substanced.widget` API
----------------------------

.. automodule:: substanced.widget

.. autofunction:: includeme

:mod:`substanced.workflow` API
------------------------------

.. automodule:: substanced.workflow
   :members:

:mod:`substanced.interfaces`
----------------------------

These represent interfaces implemented by various Substance D objects.

.. automodule:: substanced.interfaces
   :members:
