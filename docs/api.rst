.. _substanced_api:

:mod:`substanced` API
---------------------------

.. automodule:: substanced

.. autofunction:: includeme

.. autofunction:: include

.. autofunction:: scan

.. autofunction:: root_factory

:mod:`substanced.catalog` API
-----------------------------

.. automodule:: substanced.catalog

.. autoclass:: Text

.. autoclass:: Field

.. autoclass:: Keyword

.. autoclass:: Facet

.. autoclass:: Allowed

.. autoclass:: Path

.. autoclass:: Catalog
   :members:
   :inherited-members:

   .. automethod:: __setitem__

   .. automethod:: __getitem__

   Retrieve an index.

   .. automethod:: get

   Retrieve an index or return failobj.

.. autoclass:: CatalogsService
   :members:

.. autofunction:: is_catalogable

.. autofunction:: catalog_factory

.. autofunction:: includeme

.. autofunction:: add_catalog_factory

.. autofunction:: add_indexview

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

.. autoclass:: AllowedIndex
   :members:


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

.. autoclass:: NotContains

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

:mod:`hypatia.util` API
-------------------------------

.. module:: hypatia.util

.. autoclass:: ResultSet
   :members:

:mod:`substanced.content` API
-----------------------------

.. automodule:: substanced.content

.. autoclass:: content
   :members:

.. autoclass:: service
   :members:

.. autofunction:: add_content_type

.. autofunction:: add_service_type

.. autoclass:: ContentRegistry
   :members:

.. autofunction:: includeme

:mod:`substanced.dump` API
-----------------------------

.. automodule:: substanced.dump

.. autofunction:: dump

.. autofunction:: load

.. autofunction:: add_dumper

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

.. autoclass:: ACLModified
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

.. autoclass:: subscribe_acl_modified
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

:mod:`substanced.folder` API
----------------------------

.. automodule:: substanced.folder

.. autoclass:: FolderKeyError

.. autoclass:: Folder
   :members:

   .. automethod:: __init__

   .. attribute:: order

     A tuple of name values. If set, controls the order in which names should
     be returned from ``__iter__()``, ``keys()``, ``values()``, and
     ``items()``.  If not set, use an effectively random order.

.. autoclass:: SequentialAutoNamingFolder

   .. automethod:: __init__

   .. automethod:: add_next

   .. automethod:: next_name

   .. automethod:: add

.. autoclass:: RandomAutoNamingFolder

   .. automethod:: __init__

   .. automethod:: add_next

   .. automethod:: next_name

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

.. autoclass:: ReferentialIntegrityError
   :members:

.. autoclass:: SourceIntegrityError

.. autoclass:: TargetIntegrityError

:mod:`substanced.principal` API
--------------------------------

.. automodule:: substanced.principal

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

:mod:`substanced.property` API
--------------------------------

.. automodule:: substanced.property

.. autoclass:: PropertySheet

:mod:`substanced.schema` API
----------------------------

.. automodule:: substanced.schema

.. autoclass:: Schema
   :members:

.. autoclass:: NameSchemaNode

.. autoclass:: PermissionsSchemaNode

:mod:`substanced.sdi` API
----------------------------

.. automodule:: substanced.sdi

.. autofunction:: add_mgmt_view

.. autoclass:: mgmt_view

.. attribute:: LEFT

.. attribute:: MIDDLE

.. attribute:: RIGHT

.. autofunction:: includeme

:mod:`substanced.root` API
--------------------------

.. automodule:: substanced.root

.. autoclass:: Root
   :members:

:mod:`substanced.stats` API
---------------------------

.. automodule:: substanced.stats

.. autofunction:: statsd_timer

.. autofunction:: statsd_gauge

.. autofunction:: statsd_incr


:mod:`substanced.util` API
--------------------------

.. automodule:: substanced.util

.. autofunction:: acquire

.. autofunction:: get_oid

.. autofunction:: set_oid

.. autofunction:: get_acl

.. autofunction:: set_acl

.. autofunction:: get_created

.. autofunction:: set_created

.. autofunction:: get_interfaces

.. autofunction:: get_content_type

.. autofunction:: find_content

.. autofunction:: find_service

.. autofunction:: find_services

.. autofunction:: is_folder

.. autofunction:: is_service

.. autofunction:: get_factory_type

.. autofunction:: coarse_datetime_repr

.. autofunction:: postorder

.. autofunction:: merge_url_qs

.. autofunction:: chunks

.. autofunction:: renamer

.. autofunction:: get_dotted_name

.. autoclass:: Batch

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
