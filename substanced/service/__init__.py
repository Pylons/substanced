from pyramid.location import lineage

from ..interfaces import (
    IFolder,
    SERVICES_NAME
    )

def find_service(context, name):
    """ Find a service named ``name`` in the lineage of ``context`` or return
    ``None`` if no such-named service could be found."""
    for obj in lineage(context):
        if IFolder.providedBy(obj):
            services = obj.get(SERVICES_NAME)
            if services is not None:
                if name in services:
                    return services[name]
                
