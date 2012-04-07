from pyramid.location import lineage

from ..interfaces import (
    IFolder,
    SERVICES_NAME
    )

def find_service(context, name):
    for obj in lineage(context):
        if IFolder.providedBy(obj):
            services = obj.get(SERVICES_NAME)
            if services is not None:
                if name in services:
                    return services[name]
                
