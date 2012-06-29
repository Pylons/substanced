import tempfile

from zope.interface import implementer
from pyramid.threadlocal import get_current_registry

from persistent import Persistent
from BTrees.OOBTree import OOBTree
from BTrees.Length import Length

from ..interfaces import (
    IFolder,
    marker,
    SERVICES_NAME,
    )

from ..event import (
    ObjectAdded,
    ObjectWillBeAdded,
    ObjectRemoved,
    ObjectWillBeRemoved,
    )

from ..content import content

from ..service import find_service


@content(IFolder, icon='icon-folder-close', add_view='add_folder',
         name='Folder')
@implementer(IFolder)
class Folder(Persistent):
    """ A folder implementation which acts much like a Python dictionary.

    Keys must be Unicode strings; values must be arbitrary Python objects.
    """
    __tab_order__ = ('contents',)

    __name__ = None
    __parent__ = None

    # Default uses ordering of underlying BTree.
    _order = None

    def _get_order(self):
        if self._order is not None:
            return list(self._order)
        return self.data.keys()

    def _set_order(self, value):
        # XXX:  should we test against self.data.keys()?
        self._order = tuple([unicode(x) for x in value])

    def _del_order(self):
        del self._order
    order = property(_get_order, _set_order, _del_order)

    def __init__(self, data=None):
        """ Constructor.  Data may be an initial dictionary mapping object
        name to object. """
        if data is None:
            data = {}
        self.data = OOBTree(data)
        self._num_objects = Length(len(data))

    def find_service(self, service_name):
        """ Return a service named by ``service_name`` in this folder's
        ``__services__`` folder *or any parent service folder* or ``None`` if
        no such service exists."""
        return find_service(self, service_name)

    def add_service(self, name, obj):
        """ Add a service to this folder's ``__services__`` folder named
        ``name``."""
        services = self.get(SERVICES_NAME)
        if services is None:
            services = Folder()
            self.add(SERVICES_NAME, services, send_events=False,
                     allow_services=True)
        services.add(name, obj, send_events=False)

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
        object or directly decodeable to Unicode.
        """
        name = unicode(name)
        return self.data[name]

    def get(self, name, default=None):
        """ Return the object named by ``name`` or the default.

        ``name`` must be a Unicode object or a bytestring object.

        If ``name`` is a bytestring object, it must be decodable using the
        system default encoding or the UTF-8 encoding.
        """
        name = unicode(name)
        return self.data.get(name, default)

    def __contains__(self, name):
        """ Does the container contains an object named by name?

        ``name`` must be a Unicode object or a bytestring object.

        If ``name`` is a bytestring object, it must be decodable using the
        system default encoding or the UTF-8 encoding.
        """
        name = unicode(name)
        return name in self.data

    def __setitem__(self, name, other):
        """ Set object ``other' into this folder under the name ``name``.

        ``name`` must be a Unicode object or a bytestring object.

        If ``name`` is a bytestring object, it must be decodable using the
        system default encoding or the UTF-8 encoding.

        ``name`` cannot be the empty string.

        When ``other`` is seated into this folder, it will also be
        decorated with a ``__parent__`` attribute (a reference to the
        folder into which it is being seated) and ``__name__``
        attribute (the name passed in to this function.

        If a value already exists in the foldr under the name ``name``, raise
        :exc:`KeyError`.

        When this method is called, emit an
        :class:`substanced.event.ObjectWillBeAdded` event before the
        object obtains a ``__name__`` or ``__parent__`` value.  Emit an
        :class:`substanced.event.ObjectAdded` after the object obtains a
        ``__name__`` and ``__parent__`` value.
        """
        return self.add(name, other)

    def check_name(self, name, allow_services=False):
        """

        Check the ``name`` passed to ensure that it's addable to the folder.
        Returns the name decoded to Unicode if it passes all addable checks.
        It's not addable if:

        -  an object by the name already exists in the folder

        - the name is not decodeable to Unicode.

        - the name starts with ``@@`` (conflicts with explicit view names).

        - the name has slashes in it (WSGI limitation).

        - the name is empty.

        If any of these conditions are untrue, raise a :exc:`ValueError`.  If
        the name passed is ``__services__``, and ``allow_services`` is not
        ``True``, also raise a :exc:`ValueError`.
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

        if name == SERVICES_NAME and not allow_services:
            raise ValueError('%s is a reserved name' % SERVICES_NAME)

        if name.startswith('@@'):
            raise ValueError('Names which start with "@@" are not allowed')

        if '/' in name:
            raise ValueError('Names which contain a slash ("/") are not '
                             'allowed')

        if name in self.data:
            raise KeyError('An object named %s already exists' % name)

        return name

    def add(self, name, other, send_events=True,
            allow_services=False, duplicating=False):
        """ Same as ``__setitem__``.

        If ``send_events`` is False, suppress the sending of folder events.
        If ``allow_services`` is True, allow the name ``__services__`` to be
        added. if ``duplicating`` is True, oids will be replaced in
        objectmap.
        """
        name = self.check_name(name, allow_services)

        if send_events:
            event = ObjectWillBeAdded(other, self, name, duplicating)
            self._notify(event)

        other.__parent__ = self
        other.__name__ = name

        self.data[name] = other
        self._num_objects.change(1)

        if self._order is not None:
            self._order += (name,)

        if send_events:
            event = ObjectAdded(other, self, name)
            self._notify(event)

    def pop(self, name, default=marker):
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
        try:
            result = self.remove(name)
        except KeyError:
            if default is marker:
                raise
            return default
        return result

    def _notify(self, event):
        reg = get_current_registry()
        reg.subscribers((event.object, event), None)

    def __delitem__(self, name):
        """ Remove the object from this folder stored under ``name``.

        ``name`` must be a Unicode object or a bytestring object.

        If ``name`` is a bytestring object, it must be decodable using the
        system default encoding or the UTF-8 encoding.

        If no object is stored in the folder under ``name``, raise a
        :exc:`KeyError`.

        When the object stored under ``name`` is removed from this folder,
        remove its ``__parent__`` and ``__name__`` values.

        When this method is called, emit an
        :class:`substanced.event.ObjectWillBeRemoved` event before the
        object loses its ``__name__`` or ``__parent__`` values.  Emit an
        :class:`substanced.event.ObjectRemoved` after the object loses
        its ``__name__`` and ``__parent__`` value,
        """
        return self.remove(name)

    def remove(self, name, send_events=True, moving=False):
        """ Same thing as ``__delitem__``.

        If ``send_events`` is false, suppress the sending of folder events.
        If ``moving`` is True, the events sent will indicate that a move is
        in process.
        """
        name = unicode(name)
        other = self.data[name]

        if send_events:
            event = ObjectWillBeRemoved(other, self, name, moving)
            self._notify(event)

        if hasattr(other, '__parent__'):
            del other.__parent__

        if hasattr(other, '__name__'):
            del other.__name__

        del self.data[name]
        self._num_objects.change(-1)

        if self._order is not None:
            self._order = tuple([x for x in self._order if x != name])

        if send_events:
            event = ObjectRemoved(other, self, name, moving)
            self._notify(event)

        return other

    def copy(self, name, other, newname=None):
        """
        Copy a subobject named ``name`` from this folder to the folder
        represented by ``other``.  If ``newname`` is not none, it is used as
        the target object name; otherwise the existing subobject name is
        used.
        """
        if newname is None:
            newname = name

        with tempfile.TemporaryFile() as f:
            obj = self.get(name)
            obj._p_jar.exportFile(obj._p_oid, f)
            f.seek(0)
            new_obj = obj._p_jar.importFile(f)
            del new_obj.__parent__
            obj = other.add(newname, new_obj, duplicating=True)
            return obj

    def move(self, name, other, newname=None):
        """
        Move a subobject named ``name`` from this folder to the folder
        represented by ``other``.  If ``newname`` is not none, it is used as
        the target object name; otherwise the existing subobject name is
        used.

        This operation is done in terms of a remove and an add.  The Removed
        and WillBeRemoved events sent will indicate that the object is
        moving.
        """
        if newname is None:
            newname = name
        ob = self.remove(name, moving=True)
        other.add(newname, ob)
        return ob

    def rename(self, oldname, newname):
        """
        Rename a subobject from oldname to newname.

        This operation is done in terms of a remove and an add.  The Removed
        and WillBeRemoved events sent will indicate that the object is
        moving.
        """
        return self.move(oldname, self, newname)

    def replace(self, name, newobject):
        """ Replace an existing object named ``name`` in this folder with a
        new object ``newobject``.  If there isn't an object named ``name`` in
        this folder, an exception will *not* be raised; instead, the new
        object will just be added.

        This operation is done in terms of a remove and an add.  The Removed
        and WillBeRemoved events will be sent for the old object, and the
        WillBeAdded and Add events will be sent for the new object.
        """
        if name in self:
            del self[name]
        self[name] = newobject


def includeme(config): # pragma: no cover
    config.scan('.')
