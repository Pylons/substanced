from pyramid.location import lineage

from ..interfaces import (
    IFolder,
    SERVICES_NAME
    )

def _find_services(context, name, one=False):
    L = []
    for obj in lineage(context):
        if IFolder.providedBy(obj):
            services = obj.get(SERVICES_NAME)
            if services is not None:
                if name in services:
                    service = services[name]
                    if one:
                        return service
                    L.append(service)
    if one:
        return None
    return L

def find_service(context, name):
    """ Find the first service named ``name`` in the lineage of ``context``
    or return ``None`` if no such-named service could be found. """
    return _find_services(context, name, one=True)
                
def find_services(context, name):
    """Finds all services named ``name`` in the lineage of ``context`` and
    returns a sequence containing those service objects. The sequence will
    begin with the most deepest nested service and will end with the least
    deeply nested service.  Returns an empty sequence if no such-named
    service could be found."""
    return _find_services(context, name)

