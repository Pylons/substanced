from zope.interface.interfaces import IInterface

from pyramid.traversal import find_resource
from pyramid.renderers import get_renderer
from pyramid.request import Request

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
        if get_mgmt_views(request, obj):
            node['url']  = request.mgmt_path(obj)
        else:
            node['url'] = None
        L.append(node)
    return L

def get_mgmt_views(request, context=None):
    registry = request.registry
    if context is None:
        context = request.context
    introspector = registry.introspector
    L = []

    # create a dummy request signaling our intent
    req = Request(request.environ.copy())
    req.script_name = request.script_name
    req.context = context
    req.matched_route = request.matched_route
    req.method = 'GET' 

    for data in introspector.get_category('sdi views'): 
        related = data['related']
        sdi_intr = data['introspectable']
        tab_title = sdi_intr['tab_title']
        for intr in related:
            view_name = intr['name']
            if view_name == '' and tab_title == 'manage_main':
                continue # manage_main view
            if intr.category_name == 'views' and not view_name in L:
                derived = intr['derived_callable']
                # do a passable job at figuring out whether, if we visit the
                # url implied by this view, we'll be permitted to view it and
                # something reasonable will show up
                if IInterface.providedBy(intr['context']):
                    if not intr['context'].providedBy(context):
                        continue
                elif intr['context'] and not isinstance(
                        context, intr['context']):
                    continue
                req.path_info = request.mgmt_path(context, view_name)
                if hasattr(derived, '__predicated__'):
                    if not derived.__predicated__(context, req):
                        continue
                if hasattr(derived, '__permitted__'):
                    if not derived.__permitted__(context, req):
                        continue
                L.append(
                    {'view_name':view_name,
                     'tab_title':tab_title or view_name.capitalize()}
                    )
    return sorted(L)

def macros():
    template = get_renderer('views/templates/master.pt').implementation()
    return {'master':template}
