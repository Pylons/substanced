from zope.interface.interfaces import IObjectEvent

from zope.interface import (
    Interface,
    Attribute
    )

class IContent(Interface):
    """" Marker interface representing an object that has a content type """

class ICatalogable(Interface):
    """ Marker interface describing catalogable content.  An object must
    implement this interface to have its attributes indexed """

class ICatalogSite(Interface):
    """ An ICatalogSite has a ``catalog`` attribute which is an instance of a
    ``substanced.catalog.Catalog``; marker interface"""
    catalog = Attribute('a catalog')

class IDocmapSite(Interface):
    """ An IDocmapSite has a ``docmap`` attribute which is an instance of a
    ``substanced.docmap.DocumentMap``; marker interface"""
    docmap = Attribute('document map')

class ISite(ICatalogSite, IDocmapSite):
    """ Marker interface for something that is both an ICatalogSite and 
    an IDocmapSite  """

class ISearch(Interface):
    """ Adapter for searching the catalog """

class IObjectWillBeAddedEvent(IObjectEvent):
    """ An event type sent when an before an object is added """
    object = Attribute('The object being added')
    parent = Attribute('The folder to which the object is being added')
    name = Attribute('The name which the object is being added to the folder '
                     'with')

class IObjectAddedEvent(IObjectEvent):
    """ An event type sent when an object is added """
    object = Attribute('The object being added')
    parent = Attribute('The folder to which the object is being added')
    name = Attribute('The name of the object within the folder')

class IObjectWillBeRemovedEvent(IObjectEvent):
    """ An event type sent before an object is removed """
    object = Attribute('The object being removed')
    parent = Attribute('The folder from which the object is being removed')
    name = Attribute('The name of the object within the folder')

class IObjectRemovedEvent(IObjectEvent):
    """ An event type sent when an object is removed """
    object = Attribute('The object being removed')
    parent = Attribute('The folder from which the object is being removed')
    name = Attribute('The name of the object within the folder')

class IObjectModifiedEvent(IObjectEvent):
    """ May be sent when an object is modified """
    object = Attribute('The object being modified')

class IFolder(Interface):
    """ A Folder which stores objects using Unicode keys.

    All methods which accept a ``name`` argument expect the
    name to either be Unicode or a byte string decodable using the
    default system encoding or the UTF-8 encoding."""

    order = Attribute("""Order of items within the folder

    (Optional) If not set on the instance, objects are iterated in an
    arbitrary order based on the underlying data store.""")

    def keys():
        """ Return an iterable sequence of object names present in the folder.

        Respect ``order``, if set.
        """

    def __iter__():
        """ An alias for ``keys``
        """

    def values():
        """ Return an iterable sequence of the values present in the folder.

        Respect ``order``, if set.
        """

    def items():
        """ Return an iterable sequence of (name, value) pairs in the folder.

        Respect ``order``, if set.
        """

    def get(name, default=None):
        """ Return the object named by ``name`` or the default.

        ``name`` must be a Unicode object or a bytestring object.

        If ``name`` is a bytestring object, it must be decodable using the
        system default encoding or the UTF-8 encoding.
        """

    def __contains__(name):
        """ Does the container contains an object named by name?

        ``name`` must be a Unicode object or a bytestring object.

        If ``name`` is a bytestring object, it must be decodable using the
        system default encoding or the UTF-8 encoding.
        """

    def __nonzero__():
        """ Always return True
        """

    def __len__():
        """ Return the number of subobjects in this folder.
        """

    def __setitem__(name, other):
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

        When this method is called, emit an ``IObjectWillBeAddedEvent`` event
        before the object obtains a ``__name__`` or ``__parent__`` value.
        Emit an ``IObjectAddedEvent`` after the object obtains a ``__name__``
        and ``__parent__`` value.
        """

    def add(name, other, send_events=True):
        """ Same as ``__setitem__``.

        If ``send_events`` is false, suppress the sending of folder events.
        """

    def pop(name, default=None):
        """ Remove the item stored in the under ``name`` and return it.

        If ``name`` doesn't exist in the folder, and ``default`` **is not**
        passed, raise a :exc:`KeyError`.

        If ``name`` doesn't exist in the folder, and ``default`` **is**
        passed, return ``default``.

        When the object stored under ``name`` is removed from this folder,
        remove its ``__parent__`` and ``__name__`` values.

        When this method is called, emit an ``IObjectWillBeRemovedEvent`` event
        before the object loses its ``__name__`` or ``__parent__`` values.
        Emit an ``ObjectRemovedEvent`` after the object loses its ``__name__``
        and ``__parent__`` value,
        """

    def __delitem__(name):
        """ Remove the object from this folder stored under ``name``.

        ``name`` must be a Unicode object or a bytestring object.

        If ``name`` is a bytestring object, it must be decodable using the
        system default encoding or the UTF-8 encoding.

        If no object is stored in the folder under ``name``, raise a
        :exc:`KeyError`.

        When the object stored under ``name`` is removed from this folder,
        remove its ``__parent__`` and ``__name__`` values.

        When this method is called, emit an ``IObjectWillBeRemovedEvent`` event
        before the object loses its ``__name__`` or ``__parent__`` values.
        Emit an ``IObjectRemovedEvent`` after the object loses its ``__name__``
        and ``__parent__`` value,
        """

    def remove(name, send_events=True):
        """ Same thing as ``__delitem__``.

        If ``send_events`` is false, suppress the sending of folder events.
        """
    
marker = object()

