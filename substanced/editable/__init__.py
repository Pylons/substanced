from zope.interface import (
    Interface,
    implementer,
    )

from ..interfaces import IEditable
from ..file import IFile
from ..util import chunks

@implementer(IEditable)
class FileEditable(object):
    """ IEditable adapter for stock SubstanceD 'File' objects.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        """ See IEditable.
        """
        return (
            chunks(open(self.context.blob.committed(), 'rb')),
            self.context.mimetype or 'application/octet-stream',
            )

    def put(self, fp):
        """ See IEditable.
        """
        self.context.upload(fp)

def register_editable_adapter(config, adapter, iface): # pragma: no cover
    """ Configuration directive: register ``IEditable`` adapter for ``iface``.

    - ``adapter`` is the adapter factory (a class or other callable taking
      ``(context, request)``).

    - ``iface`` is the interface / class for which the adapter is registered.
    """
    def register():
        intr['registered'] = adapter
        config.registry.registerAdapter(adapter, (iface, Interface), IEditable)

    discriminator = ('sd-editable-adapter', iface)
    intr = config.introspectable(
        'sd editable adapters',
        discriminator,
        iface.__name__,
        'sd editable adapter'
        )
    intr['adapter'] = adapter

    config.action(discriminator, callable=register, introspectables=(intr,))

def get_editable_adapter(context, request):
    """ Return an editable adapter for the context
    
    Return ``None`` if no editable adapter is registered.
    """
    adapter = request.registry.queryMultiAdapter(
        (context, request),
        IEditable
        )
    return adapter
    

def includeme(config): # pragma: no cover
    config.add_directive('register_editable_adapter', register_editable_adapter)
    config.register_editable_adapter(FileEditable, IFile)
