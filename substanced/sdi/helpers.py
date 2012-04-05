from zope.interface.interfaces import IInterface
from zope.interface import Interface

from pyramid.traversal import find_resource
from pyramid.renderers import get_renderer
from pyramid.security import (
    view_execution_permitted,
    has_permission,
    )

from substanced.objectmap import find_objectmap

MANAGE_ROUTE_NAME = 'substanced_manage'

def get_subnodes(request, context=None):
    if context is None:
        context = request.context
    objectmap = find_objectmap(context)
    nodes = objectmap.navgen(context, depth=1)
    L = []
    for node in nodes:
        obj = find_resource(context, node['path'])
        if has_permission('view', obj, request):
            node['url'] = request.mgmt_path(obj)
            L.append(node)
    return L

def get_mgmt_views(request, context=None):
    registry = request.registry
    if context is None:
        context = request.context
    introspector = registry.introspector
    L = []
    for data in introspector.get_category('views'): 
        intr = data['introspectable']
        route_name = intr['route_name']
        if route_name == MANAGE_ROUTE_NAME:
            iface = intr['context'] or Interface
            if IInterface.providedBy(iface):
                ok = iface.providedBy(context)
            else:
                ok = context.__class__ == iface
            if ok:
                view_name = intr['name']
                if view_name:
                    if view_execution_permitted(context, request,view_name):
                        if not view_name in L:
                            L.append(view_name)
    return sorted(L)

def macros():
    template = get_renderer('templates/master.pt').implementation()
    return {'master':template}
