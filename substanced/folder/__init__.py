import random
import string

from zope.interface import implementer
from zope.copy.interfaces import (
    ICopyHook,
    ResumeCopy
    )

from zope.copy import copy

from persistent import (
    Persistent,
    )

from persistent.interfaces import IPersistent

import BTrees
from BTrees.Length import Length

from pyramid.location import (
    lineage,
    inside,
    )
from pyramid.threadlocal import get_current_registry
from pyramid.traversal import resource_path_tuple

from ..interfaces import (
    IFolder,
    IAutoNamingFolder,
    marker,
    )

from ..content import content

from ..event import (
    ObjectAdded,
    ObjectWillBeAdded,
    ObjectRemoved,
    ObjectWillBeRemoved,
    )

from ..util import (
    get_oid,
    postorder,
    find_service,
    find_services,
    )

from ..objectmap import find_objectmap

class FolderKeyError(KeyError):
    pass

@content(
    'Folder',
    icon='icon-folder-close',
    add_view='add_folder',
    )
@implementer(IFolder)
class Folder(Persistent):
    """ A folder implementation which acts much like a Python dictionary.

    Keys must be Unicode strings; values must be arbitrary Python objects.
    """
    family = BTrees.family64

    __name__ = None
    __parent__ = None

    # Default uses ordering of underlying BTree.
    _order = None

    def _get_order(self):
        if self._order is not None:
            return self._order
        return self.data.keys()

    def _set_order(self, value):
        # XXX:  should we test against self.data.keys()?
        self._order = tuple([unicode(x) for x in value])

    def _del_order(self):
        del self._order

    order = property(_get_order, _set_order, _del_order)

    def is_ordered(self):
        """ Return true if the folder is manually ordered, false otherwise. """
        return self._order is not None

    def __init__(self, data=None, family=None):
        """ Constructor.  Data may be an initial dictionary mapping object
        name to object. """
        if family is not None:
            self.family = family
        if data is None:
            data = {}
        self.data = self.family.OO.BTree(data)
        self._num_objects = Length(len(data))

    def find_service(self, service_name):
        """ Return a service named by ``service_name`` in this folder *or any
        parent service folder* or ``None`` if no such service exists.  A
        shortcut for :func:`substanced.service.find_service`."""
        return find_service(self, service_name)

    def find_services(self, service_name):
        """ Returns a sequence of service objects named by ``service_name``
        in this folder's lineage or an empty sequence if no such service
        exists.  A shortcut for :func:`substanced.service.find_services`"""
        return find_services(self, service_name)

    def add_service(self, name, obj, registry=None, **kw):
        """ Add a service to this folder named ``name``."""
        if registry is None:
            registry = get_current_registry()
        kw['registry'] = registry
        self.add(name, obj, **kw)
        obj.__is_service__ = True

    def keys(self):
        """ Return an iterable sequence of object names present in the folder.

        Respect ``order``, if set.
        """
        return self.order

    def __iter__(self):
        """ An alias for ``keys``
        """
        return iter(self.order)

    def values(self):
        """ Return an iterable sequence of the values present in the folder.

        Respect ``order``, if set.
        """
        if self._order is not None:
            return [self.data[name] for name in self.order]
        return self.data.values()

    def items(self):
        """ Return an iterable sequence of (name, value) pairs in the folder.

        Respect ``order``, if set.
        """
        if self._order is not None:
            return [(name, self.data[name]) for name in self.order]
        return self.data.items()

    def __len__(self):
        """ Return the number of objects in the folder.
        """
        return self._num_objects()

    def __nonzero__(self):
        """ Return ``True`` unconditionally.
        """
        return True

    def __repr__(self):
        klass = self.__class__
        classname = '%s.%s' % (klass.__module__, klass.__name__)
        return '<%s object %r at %#x>' % (classname,
                                          self.__name__,
                                          id(self))

    def __getitem__(self, name):
        """ Return the object named ``name`` added to this folder or raise
        ``KeyError`` if no such object exists.  ``name`` must be a Unicode
        object or directly decodeable to Unicode using the system default
        encoding.
        """
        name = unicode(name)
        return self.data[name]

    def get(self, name, default=None):
        """ Return the object named by ``name`` or the default.

        ``name`` must be a Unicode object or a bytestring object.

        If ``name`` is a bytestring object, it must be decodable using the
        system default encoding.
        """
        name = unicode(name)
        return self.data.get(name, default)

    def __contains__(self, name):
        """ Does the container contains an object named by name?

        ``name`` must be a Unicode object or a bytestring object.

        If ``name`` is a bytestring object, it must be decodable using the
        system default encoding.
        """
        name = unicode(name)
        return name in self.data

    def __setitem__(self, name, other):
        """ Set object ``other' into this folder under the name ``name``.

        ``name`` must be a Unicode object or a bytestring object.

        If ``name`` is a bytestring object, it must be decodable using the
        system default encoding.

        ``name`` cannot be the empty string.

        When ``other`` is seated into this folder, it will also be decorated
        with a ``__parent__`` attribute (a reference to the folder into which
        it is being seated) and ``__name__`` attribute (the name passed in to
        this function.  It must not already have a ``__parent__`` attribute
        before being seated into the folder, or an exception will be raised.

        If a value already exists in the foldr under the name ``name``, raise
        :exc:`KeyError`.

        When this method is called, the object will be added to the objectmap,
        an :class:`substanced.event.ObjectWillBeAdded` event will be emitted
        before the object obtains a ``__name__`` or ``__parent__`` value, then
        a :class:`substanced.event.ObjectAdded` will be emitted after the
        object obtains a ``__name__`` and ``__parent__`` value.
        """
        return self.add(name, other)

    def validate_name(self, name, reserved_names=()):
        """
        Validate the ``name`` passed to ensure that it's addable to the folder.
        Returns the name decoded to Unicode if it passes all addable checks.
        It's not addable if:

        - the name is not decodeable to Unicode.

        - the name starts with ``@@`` (conflicts with explicit view names).

        - the name has slashes in it (WSGI limitation).

        - the name is empty.

        If any of these conditions are untrue, raise a :exc:`ValueError`.  If
        the name passed is in the list of ``reserved_names``, raise a
        :exc:`ValueError`.
        """
        if not isinstance(name, basestring):
            raise ValueError("Name must be a string rather than a %s" %
                             name.__class__.__name__)
        if not name:
            raise ValueError("Name must not be empty")

        try:
            name = unicode(name)
        except UnicodeDecodeError:
            raise ValueError('Name "%s" not decodeable to unicode' % name)

        if name in reserved_names:
            raise ValueError('%s is a reserved name' % name)

        if name.startswith('@@'):
            raise ValueError('Names which start with "@@" are not allowed')

        if '/' in name:
            raise ValueError('Names which contain a slash ("/") are not '
                             'allowed')

        return name

    def check_name(self, name, reserved_names=()):
        """ Perform all the validation checks implied by
        :meth:`~substanced.folder.Folder.validate_name` against the ``name``
        supplied but also fail with a
        :class:`~substanced.folder.FolderKeyError` if an object with the name
        ``name`` already exists in the folder."""

        name = self.validate_name(name, reserved_names=reserved_names)

        if name in self.data:
            raise FolderKeyError('An object named %s already exists' % name)

        return name

    def add(self, name, other, send_events=True, reserved_names=(),
            duplicating=None, moving=None, loading=False, registry=None):
        """ Same as ``__setitem__``.

        If ``send_events`` is False, suppress the sending of folder events.
        Don't allow names in the ``reserved_names`` sequence to be added.

        If ``duplicating`` not ``None``, it must be the object which is being
        duplicated; a result of a non-``None`` duplicating means that oids will
        be replaced in objectmap.  If ``moving`` is not ``None``, it must be
        the folder from which the object is moving; this will be the ``moving``
        attribute of events sent by this function too.  If ``loading`` is
        ``True``, the ``loading`` attribute of events sent as a result of
        calling this method will be ``True`` too.

        This method returns the name used to place the subobject in the
        folder (a derivation of ``name``, usually the result of
        ``self.check_name(name)``).
        """
        if registry is None:
            registry = get_current_registry()

        name = self.check_name(name, reserved_names)

        if getattr(other, '__parent__', None):
            raise ValueError(
                'obj %s added to folder %s already has a __parent__ attribute, '
                'please remove it completely from its existing parent (%s) '
                'before trying to readd it to this one' % (
                    other, self, self.__parent__)
                )

        objectmap = find_objectmap(self)

        if objectmap is not None:

            basepath = resource_path_tuple(self)

            for node in postorder(other):
                node_path = node_path_tuple(node)
                path_tuple = basepath + (name,) + node_path[1:]
                # the below gives node an objectid; if the will-be-added event
                # is the result of a duplication, replace the oid of the node
                # with a new one
                objectmap.add(
                    node,
                    path_tuple,
                    duplicating=duplicating is not None,
                    moving=moving is not None,
                    )

        if send_events:
            event = ObjectWillBeAdded(
                other, self, name, duplicating=duplicating, moving=moving,
                loading=loading,
                )
            self._notify(event, registry)

        other.__parent__ = self
        other.__name__ = name

        self.data[name] = other
        self._num_objects.change(1)

        if self._order is not None:
            self._order += (name,)

        if send_events:
            event = ObjectAdded(
                other, self, name, duplicating=duplicating, moving=moving,
                loading=loading,
                )
            self._notify(event, registry)

        return name

    def pop(self, name, default=marker, registry=None):
        """ Remove the item stored in the under ``name`` and return it.

        If ``name`` doesn't exist in the folder, and ``default`` **is not**
        passed, raise a :exc:`KeyError`.

        If ``name`` doesn't exist in the folder, and ``default`` **is**
        passed, return ``default``.

        When the object stored under ``name`` is removed from this folder,
        remove its ``__parent__`` and ``__name__`` values.

        When this method is called, emit an
        :class:`substanced.event.ObjectWillBeRemoved` event before the
        object loses its ``__name__`` or ``__parent__`` values.  Emit an
        :class:`substanced.event.ObjectRemoved` after the object loses its
        ``__name__`` and ``__parent__`` value,
        """
        if registry is None:
            registry = get_current_registry()
        try:
            result = self.remove(name, registry=registry)
        except KeyError:
            if default is marker:
                raise
            return default
        return result

    def _notify(self, event, registry=None):
        if registry is None:
            registry = get_current_registry()
        registry.subscribers((event, event.object, self), None)

    def __delitem__(self, name):
        """ Remove the object from this folder stored under ``name``.

        ``name`` must be a Unicode object or a bytestring object.

        If ``name`` is a bytestring object, it must be decodable using the
        system default encoding.

        If no object is stored in the folder under ``name``, raise a
        :exc:`KeyError`.

        When the object stored under ``name`` is removed from this folder,
        remove its ``__parent__`` and ``__name__`` values.

        When this method is called, the removed object will be removed from the
        objectmap, a :class:`substanced.event.ObjectWillBeRemoved` event will
        be emitted before the object loses its ``__name__`` or ``__parent__``
        values and a :class:`substanced.event.ObjectRemoved` will be emitted
        after the object loses its ``__name__`` and ``__parent__`` value,
        """
        return self.remove(name)

    def remove(self, name, send_events=True, moving=None, loading=False,
               registry=None):
        """ Same thing as ``__delitem__``.

        If ``send_events`` is false, suppress the sending of folder events.

        If ``moving`` is not ``None``, the ``moving`` argument must be the
        folder to which the named object will be moving.  This value will be
        passed along as the ``moving`` attribute of the events sent as the
        result of this action.  If ``loading`` is ``True``, the ``loading``
        attribute of events sent as a result of calling this method will be
        ``True`` too.
        """
        name = unicode(name)
        other = self.data[name]
        oid = get_oid(other, None)

        if registry is None:
            registry = get_current_registry()

        if send_events:
            event = ObjectWillBeRemoved(
                other, self, name, moving=moving, loading=loading
                )
            self._notify(event, registry)

        if hasattr(other, '__parent__'):
            del other.__parent__

        if hasattr(other, '__name__'):
            del other.__name__

        del self.data[name]
        self._num_objects.change(-1)

        if self._order is not None:
            self._order = tuple([x for x in self._order if x != name])

        objectmap = find_objectmap(self)

        removed_oids = set([oid])

        if objectmap is not None and oid is not None:
            removed_oids = objectmap.remove(oid, moving=moving is not None)

        if send_events:
            event = ObjectRemoved(other, self, name, removed_oids,
                                  moving=moving, loading=loading)
            self._notify(event, registry)

        return other

    def copy(self, name, other, newname=None, registry=None):
        """
        Copy a subobject named ``name`` from this folder to the folder
        represented by ``other``.  If ``newname`` is not none, it is used as
        the target object name; otherwise the existing subobject name is
        used.
        """
        if newname is None:
            newname = name

        if registry is None:
            registry = get_current_registry()

        obj = self[name]
        newobj = copy(obj)
        return other.add(newname, newobj, duplicating=obj, registry=registry)

    def move(self, name, other, newname=None, registry=None):
        """
        Move a subobject named ``name`` from this folder to the folder
        represented by ``other``.  If ``newname`` is not none, it is used as
        the target object name; otherwise the existing subobject name is
        used.

        This operation is done in terms of a remove and an add.  The Removed
        and WillBeRemoved events as well as the Added and WillBeAdded events
        sent will indicate that the object is moving.
        """
        if newname is None:
            newname = name
        if registry is None:
            registry = get_current_registry()
        ob = self.remove(
            name,
            moving=other,
            registry=registry
            )
        other.add(
            newname,
            ob,
            moving=self,
            registry=registry
            )
        return ob

    def rename(self, oldname, newname, registry=None):
        """
        Rename a subobject from oldname to newname.

        This operation is done in terms of a remove and an add.  The Removed
        and WillBeRemoved events sent will indicate that the object is
        moving.
        """
        if registry is None:
            registry = get_current_registry()
        return self.move(oldname, self, newname, registry=registry)

    def replace(self, name, newobject, send_events=True, registry=None):
        """ Replace an existing object named ``name`` in this folder with a
        new object ``newobject``.  If there isn't an object named ``name`` in
        this folder, an exception will *not* be raised; instead, the new
        object will just be added.

        This operation is done in terms of a remove and an add.  The Removed
        and WillBeRemoved events will be sent for the old object, and the
        WillBeAdded and Added events will be sent for the new object.
        """
        if registry is None:
            registry = get_current_registry()
        if name in self:
            self.remove(name, send_events=send_events)
        self.add(name, newobject, send_events=send_events, registry=registry)

    def load(self, name, newobject, registry=None):
        """ A replace method used by the code that loads an existing dump.
        Events sent during this replace will have a true ``loading`` flag."""
        if registry is None:
            registry = get_current_registry()
        if name in self:
            self.remove(name, loading=True)
        self.add(name, newobject, loading=True, registry=registry)

class _AutoNamingFolder(object):
    def add_next(
        self,
        subobject,
        send_events=True,
        duplicating=None,
        moving=None,
        registry=None
        ):
        """Add a subobject, naming it automatically, giving it the name
        returned by this folder's ``next_name`` method.  It has the same
        effect as calling :meth:`substanced.folder.Folder.add`, but you
        needn't provide a name argument.

        This method returns the name of the subobject.
        """

        name = self.next_name(subobject)

        return self.add(
            name,
            subobject,
            send_events=send_events,
            duplicating=duplicating,
            moving=moving,
            registry=registry
            )

@implementer(IAutoNamingFolder)
class SequentialAutoNamingFolder(Folder, _AutoNamingFolder):
    """ An auto-naming folder which autonames a subobject by sequentially
    incrementing the maximum key of the folder.

    Example names: ``0000001``, then ``0000002``, and so on.

    This class implements the
    :class:`substanced.interfaces.IAutoNamingFolder` interface and inherits
    from :class:`substanced.folder.Folder`.

    This class is typically used as a base class for a custom content type.
    """

    _autoname_length = 7
    _autoname_start = -1

    def __init__(
        self,
        data=None,
        family=None,
        autoname_length=None,
        autoname_start=None
        ):
        """ Constructor.  Data may be an initial dictionary mapping object
        name to object. Autoname length may be supplied.  If it is not, it
        will default to 7.  Autoname start may be supplied.  If it is not, it
        will default to -1."""
        if autoname_length is not None:
            self._autoname_length = autoname_length
        if autoname_start is not None:
            self._autoname_start = autoname_start

        super(SequentialAutoNamingFolder, self).__init__(
            data=data,
            family=family,
            )

    def next_name(self, subobject):
        """Return a name string based on:

        - intifying the maximum key of this folder and adding one.

        - zero-filling the left hand side of the result with as many zeroes
          as are in the value of this folder's ``autoname_length``
          constructor value.

        If the folder has no items in it, the initial value used as a name
        will be the value of this folder's ``autoname_start`` constructor
        value.
        """
        try:
            maxkey = self.data.maxKey()
        except ValueError: # empty tree
            maxkey = self._autoname_start
        name = self._zfill(int(maxkey) + 1)
        return name

    def _zfill(self, name):
        return str(int(name)).zfill(self._autoname_length)

    def add(self, name, other, send_events=True, reserved_names=(),
            duplicating=None, moving=None, loading=False, registry=None):
        """ The ``add`` method of a SequentialAutoNamingFolder will raise a
        :exc:`ValueError` if the ``name`` it is passed is not intifiable, as
        its ``next_name`` method relies on controlling the types of names
        that are added to it (they must be intifiable).  It will also
        zero-fill the name passed based on this folder's ``autoname_length``
        constructor value.  It otherwise just calls its superclass' ``add``
        method and returns the result."""
        try:
            int(name)
        except:
            raise ValueError(
                'You cannot call the add method of a %s with a name that '
                'is not intifiable; you passed %r' % (
                    self.__class__.__name__,
                    name
                    )
            )
        name = self._zfill(name)
        return super(SequentialAutoNamingFolder, self).add(
            name,
            other,
            send_events=send_events,
            reserved_names=reserved_names,
            duplicating=duplicating,
            moving=moving,
            loading=loading,
            registry=registry,
            )

@implementer(IAutoNamingFolder)
class RandomAutoNamingFolder(Folder, _AutoNamingFolder):
    """An auto-naming folder which autonames a subobject using a random
    string.

    Example names: ``MXF937A``, ``FLTP2F9``.

    This class implements the
    :class:`substanced.interfaces.IAutoNamingFolder` interface and inherits
    from :class:`substanced.folder.Folder`.

    This class is typically used as a base class for a custom
    content type.    
    """

    _randomchoice = staticmethod(random.choice) # for testing
    _autoname_length = 7

    def __init__(self, data=None, family=None, autoname_length=None):
        """ Constructor.  Data may be an initial dictionary mapping object
        name to object. Autoname length may be supplied.  If it is not, it
        will default to 7."""
        if autoname_length is not None:
            self._autoname_length = autoname_length

        super(RandomAutoNamingFolder, self).__init__(
            data=data,
            family=family,
            )

    def next_name(self, subobject):
        """Return a name string based on generating a random string composed
        of digits and uppercase letters of a length determined by this
        folder's ``autoname_length`` constructor value.  It tries generatoing
        values continuously until one that is unused is found.
        """
        def randchar():
            return self._randomchoice(
                string.ascii_uppercase + string.digits
                )
        while True:
            name = ''.join([randchar() for x in range(self._autoname_length)])
            if not name in self:
                return name

def node_path_tuple(resource):
    # cant use resource_path_tuple from pyramid, it wants everything to 
    # have a __name__
    return tuple(reversed([getattr(loc, '__name__', '') for 
                           loc in lineage(resource)]))

class CopyHook(object):
    def __init__(self, context):
        self.context = context
    
    def __call__(self, toplevel, register):
        context = self.context
        # We can't register for a more specific interface than IPersistent so
        # we have to check for __parent__ here (signifiying that the object is
        # located) and do something special rather than just registering a copy
        # hook for things that are guaranteed to have a __parent__ (such as
        # Zope's ILocation)
        if hasattr(context, '__parent__'):
            if not inside(self.context, toplevel):
                # Return the object if we *don't* want it copied.  I don't
                # really quite understand why we return it instead of returning
                # None, and why we raise an exception if we *do* want it copied
                # but mine is not to wonder why.
                return context
        # Otherwise, it's a persistent object that does live inside the object
        # we're copying or a nonpersistent object.  In such cases, we
        # definitely want to copy them and we signify this desire by raising
        # ResumeCopy.
        raise ResumeCopy

def includeme(config): # pragma: no cover
    # The ICopyHook adapter avoids dumping referenced objects that are not
    # located inside an object containment-wise when that object is copied.  If
    # it is not registered, every copy winds up dumping all the objects in the
    # database due to __parent__ pointers.
    config.registry.registerAdapter(CopyHook, (IPersistent,), ICopyHook)
    config.hook_zca() # required by zope.copy (it uses a global adapter lkup)
    
