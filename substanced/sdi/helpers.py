from pyramid.traversal import find_resource

from substanced.objectmap import find_objectmap

def get_subnodes(request, context=None):
    if context is None:
        context = request.context
    objectmap = find_objectmap(context)
    nodes = objectmap.navgen(context, depth=1)
    for node in nodes:
        obj = find_resource(context, node['path'])
        node['url'] = request.mgmt_path(obj)
    return nodes

