import random
import string
import tempfile

from zope.interface import implementer
from pyramid.threadlocal import get_current_registry
from pyramid.security import has_permission

from persistent import Persistent

import BTrees
from BTrees.Length import Length

from ..exceptions import FolderKeyError

from ..interfaces import (
    IFolder,
    IAutoNamingFolder,
    marker,
    SERVICES_NAME,
    RESERVED_NAMES,
    )

from ..event import (
    ObjectAdded,
    ObjectWillBeAdded,
    ObjectRemoved,
    ObjectWillBeRemoved,
    )

from ..content import (
    content,
    find_service,
    find_services,
    )

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

    def __sd_columns__(self, folder, subobject, request):
        name = getattr(subobject, '__name__', '')
        url = request.mgmt_path(subobject, '@@manage_main')
        link_tag = '<a href="%s">%s</a>' % (url, name)
        icon = request.registry.content.metadata(subobject, 'icon')
        if callable(icon):
            icon = icon(subobject, request)
        icon_tag = '<i class="%s"> </i>' % icon
        return [{'name': 'Name',
                'value': '%s %s' % (icon_tag, link_tag),
                'sortable': True}]

    def __sd_buttons__(self, context, request):
        buttons = []
        finish_buttons = []

        if 'tocopy' in request.session:
            finish_buttons.extend(
                [
                {'id': 'copy_finish',
                  'name': 'copy_finish',
                  'class': 'btn-primary',
                  'value': 'copy_finish',
                  'text': 'Copy here'},
                {'id': 'cancel',
                 'name': 'copy_finish',
                 'class': 'btn-danger',
                 'value': 'cancel',
                 'text': 'Cancel'},
                ])

        if 'tomove' in request.session:
            finish_buttons.extend(
                [{'id': 'move_finish',
                  'name': 'move_finish',
                  'class': 'btn-primary',
                  'value': 'move_finish',
                  'text': 'Move here'},
                 {'id': 'cancel',
                  'name': 'move_finish',
                  'class': 'btn-danger',
                  'value': 'cancel',
                  'text': 'Cancel'}])

        if finish_buttons:
            buttons.append(
              {'type':'single', 'buttons':finish_buttons}
              )

        if not 'tomove' in request.session and not 'tocopy' in request.session:

            main_buttons = [
                 {'id': 'rename',
                  'name': 'rename',
                  'class': '',
                  'value': 'rename',
                  'text': 'Rename'},
                  {'id': 'copy',
                  'name': 'copy',
                  'class': '',
                  'value': 'copy',
                  'text': 'Copy'},
                  {'id': 'move',
                  'name': 'move',
                  'class': '',
                  'value': 'move',
                  'text': 'Move'},
                  {'id': 'duplicate',
                  'name': 'duplicate',
                  'class': '',
                  'value': 'duplicate',
                  'text': 'Duplicate'}
                  ]

            buttons.append({'type': 'group', 'buttons':main_buttons})

            delete_buttons = [
                  {'id': 'delete',
                   'name': 'delete',
                   'class': 'btn-danger',
                   'value': 'delete',
                   'text': 'Delete'}
                   ]

            buttons.append({'type': 'group', 'buttons':delete_buttons})

        return buttons


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
        """ Return a service named by ``service_name`` in this folder's
        ``__services__`` folder *or any parent service folder* or ``None`` if
        no such service exists.  A shortcut for
        :func:`substanced.service.find_service`."""
        return find_service(self, service_name)

    def find_services(self, service_name):
        """ Returns a sequence of service objects named by ``service_name``
        in this folder's lineage or an empty sequence if no such service
        exists.  A shortcut for :func:`substanced.service.find_services`"""
        return find_services(self, service_name)

    def add_service(self, name, obj, registry=None):
        """ Add a service to this folder's ``__services__`` folder named
        ``name``."""
        if registry is None:
            registry = get_current_registry()
        services = self.get(SERVICES_NAME)
        if services is None:
            services = registry.content.create('Services')
            self.add(SERVICES_NAME, services, reserved_names=())
        services.add(name, obj)

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

    def check_name(self, name, reserved_names=RESERVED_NAMES):
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

        if name in self.data:
            raise FolderKeyError('An object named %s already exists' % name)

        return name

    def add(self, name, other, send_events=True, reserved_names=RESERVED_NAMES,
            duplicating=False, registry=None):
        """ Same as ``__setitem__``.

        If ``send_events`` is False, suppress the sending of folder events.
        Don't allow names in the ``reserved_names`` sequence to be
        added. If ``duplicating`` is True, oids will be replaced in
        objectmap.

        This method returns the name used to place the subobject in the
        folder (a derivation of ``name``, usually the result of
        ``self.check_name(name)``).
        """
        if registry is None:
            registry = get_current_registry()
        name = self.check_name(name, reserved_names)

        if send_events:
            event = ObjectWillBeAdded(other, self, name, duplicating)
            self._notify(event, registry)

        other.__parent__ = self
        other.__name__ = name

        self.data[name] = other
        self._num_objects.change(1)

        if self._order is not None:
            self._order += (name,)

        if send_events:
            event = ObjectAdded(other, self, name)
            self._notify(event, registry)

        return name

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

def add_services_folder(context, request):
    if IFolder.providedBy(context):
        if not '__services__' in context:
            return 'add_services_folder'

@content(
    'Services',
    icon='icon-off',
    add_view=add_services_folder,
    )
class Services(Folder):
    def __sd_addable__(self, introspectable):
        # The only kinds of objects addable to a Services folder are
        # services, so we return True iff:
        #
        # - The introspectable represents a content type registered with the
        # @service decorator or config.add_service (it adds ``is_service`` to
        # the type's metadata).
        #
        # - The service name mentioned in the introspectable metadata doesn't
        #   already exist in this services folder.  If the introspectable
        #   metadata doesn't mention a service name, however, this condition
        #   is elided.
        meta = introspectable['meta']
        is_service = meta.get('is_service', False)
        if is_service:
            service_name = meta.get('service_name', None)
            return not (service_name and service_name in self)
        return False

    def __sd_hidden__(self, context, request):
        # Don't show this item in folder contents view unless the viewer
        # has permission to add services in the SDI
        return not has_permission('sdi.add-services', context, request)

class _AutoNamingFolder(object):
    def add_next(
        self,
        subobject,
        send_events=True,
        duplicating=False,
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

    def add(self, name, other, send_events=True, reserved_names=RESERVED_NAMES,
            duplicating=False, registry=None):
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

def includeme(config): # pragma: no cover
    config.scan('.')
