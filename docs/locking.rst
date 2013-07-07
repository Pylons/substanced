==============
Using Locking
==============

Substance D allows you to lock content resources programmatically.  When a
resource is locked, its UI can change to indicate that it cannot be edited by
someone other than the user holding the lock.

Locking a resource *only* locks the resource, not its children.  The locking
system is not recursive at this time.

Locking a Resource
==================

To lock a resource:

.. code-block:: python

   from substanced.locking import lock_resource
   from pyramid.security import has_permission

   if has_permission('sdi.lock', someresource, request):
       lock_resource(someresource, request.user, timeout=3600)

If the resource is already locked by the owner supplied as ``owner_or_ownerid``
(the parameter filled by ``request.user`` above), calling this function will
refresh the lock.  If the resource is not already locked by another user,
calling this function will create a new lock.  If the resource is already
locked by a different user, a :class:`substanced.locking.LockError` will be
raised.

Using the :func:`substanced.locking.lock_resource` function has the side effect
of creating a "Lock Service" (named ``locks``) in the Substance D root if one
does not already exist.

.. warning::

   Callers should assert that the owner has the ``sdi.lock`` permission against
   the resource before calling :func:`~substanced.locking.lock_resource` to
   ensure that a user can't lock a resource he is not permitted to.

Locking a Resource
==================

To unlock a resource:

.. code-block:: python

   from substanced.locking import unlock_resource
   from pyramid.security import has_permission

   if has_permission('sdi.lock', someresource, request):
       unlock_resource(someresource, request.user, timeout=3600)

If the resource is already locked by a user other than the owner supplied as
``owner_or_ownerid`` (the parameter filled by ``request.user`` above) or the
resource isn't already locked with this lock type, calling this function will
raise a :class:`substanced.locking.LockError` exception.  Otherwise the lock
will be removed.

Using the :func:`substanced.locking.unlock_resource` function has the side
effect of creating a "Lock Service" (named ``locks``) in the Substance D root
if one does not already exist.

.. warning::

   Callers should assert that the owner has the ``sdi.lock`` permission against
   the resource before calling :func:`~substanced.locking.unlock_resource` to
   ensure that a user can't lock a resource he is not permitted to.

Discovering Existing Locks
==========================

To discover any existing locks for a resource:

.. code-block:: python

   from substanced.locking import discover_resource_locks

   locks = discover_resource_locks(someresource)
   # "locks" will be a sequence

The :func:`substanced.locking.discover_resource_locks` function will return a
sequence of :class:`substanced.locking.Lock` objects related to the resource
for the lock type provided to the function.  By default, only valid locks are
returned.  Invalid locks for the resource may exist, but they are not returned
unless the ``include_invalid`` argument passed to
::func:`~substanced.locking.discover_resource_locks` is ``True``.

Under normal circumstances, the length of the sequence returned will be either
0 (if there are no locks) or 1 (if there is any lock).  In some special
circumstances, however, when the :class:`substanced.locking.lock_resource` API
is not used to create locks, there may be more than one lock related to a
resource of the same type.

Viewing The Lock Service
========================

Once some locks have been created, a *lock service* will have been created.
The lock service is an object named ``locks`` in the Substance D root.

You can use the SDI UI of this locks service to delete and edit existing locks.
It's a good idea to periodically use the "Delete Expired" button in this UI to
clear out any existing expired locks that were orphaned by buggy or interrupted
clients.