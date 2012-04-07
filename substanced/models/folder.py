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

from ..events import (
    ObjectAddedEvent,
    ObjectWillBeAddedEvent,
    ObjectRemovedEvent,
    ObjectWillBeRemovedEvent,
    )

from ..service import find_service

@implementer(IFolder)
class Folder(Persistent):
    """ A folder implementation which acts much like a Python dictionary.

    Keys must be Unicode strings; values must be arbitrary Python objects.
    """

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
        if data is None:
            data = {}
        self.data = OOBTree(data)
        self._num_objects = Length(len(data))

    def keys(self):
        """ See IFolder.
        """
        return self.order

    def get_service(self, service_name):
        return find_service(self, service_name)

    def __iter__(self):
        return iter(self.order)

    def values(self):
        """ See IFolder.
        """
        if self._order is not None:
            return [self.data[name] for name in self.order]
        return self.data.values()

    def items(self):
        """ See IFolder.
        """
        if self._order is not None:
            return [(name, self.data[name]) for name in self.order]
        return self.data.items()

    def __len__(self):
        """ See IFolder.
        """
        return self._num_objects()

    def __nonzero__(self):
        """ See IFolder.
        """
        return True

    def __getitem__(self, name):
        """ See IFolder.
        """
        name = unicode(name)
        return self.data[name]

    def get(self, name, default=None):
        """ See IFolder.
        """
        name = unicode(name)
        return self.data.get(name, default)

    def __contains__(self, name):
        """ See IFolder.
        """
        name = unicode(name)
        return self.data.has_key(name)

    def __setitem__(self, name, other):
        """ See IFolder.
        """
        return self.add(name, other)

    def add(self, name, other, send_events=True, allow_services=False):
        """ See IFolder.
        """
        if not isinstance(name, basestring):
            raise TypeError("Name must be a string rather than a %s" %
                            name.__class__.__name__)
        if not name:
            raise TypeError("Name must not be empty")

        if name == SERVICES_NAME and not allow_services:
            raise KeyError('%s is a reserved name' % SERVICES_NAME)
        
        name = unicode(name)

        if self.data.has_key(name):
            raise KeyError('An object named %s already exists' % name)

        if send_events:
            event = ObjectWillBeAddedEvent(other, self, name)
            self._notify(event)
        other.__parent__ = self
        other.__name__ = name

        self.data[name] = other
        self._num_objects.change(1)

        if self._order is not None:
            self._order += (name,)

        if send_events:
            event = ObjectAddedEvent(other, self, name)
            self._notify(event)

    def add_service(self, name, obj):
        services = self.get(SERVICES_NAME)
        if services is None:
            services = Folder()
            self.add(SERVICES_NAME, services, send_events=False, 
                     allow_services=True)
        services.add(name, obj, send_events=False)

    def _notify(self, event):
        reg = get_current_registry()
        reg.subscribers((event.object, event), None)

    def __delitem__(self, name):
        """ See IFolder.
        """
        return self.remove(name)

    def remove(self, name, send_events=True):
        """ See IFolder.
        """
        name = unicode(name)
        other = self.data[name]

        if send_events:
            event = ObjectWillBeRemovedEvent(other, self, name)
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
            event = ObjectRemovedEvent(other, self, name)
            self._notify(event)

        return other

    def pop(self, name, default=marker):
        """ See IFolder.
        """
        try:
            result = self.remove(name)
        except KeyError:
            if default is marker:
                raise
            return default
        return result

    def __repr__(self):
        klass = self.__class__
        classname = '%s.%s' % (klass.__module__, klass.__name__)
        return '<%s object %r at %#x>' % (classname,
                                          self.__name__,
                                          id(self))

