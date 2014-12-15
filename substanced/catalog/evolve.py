from substanced.catalog.indexes import PathIndex
from substanced.util import get_dotted_name
from substanced.objectmap import find_objectmap

def treesetify_catalog_pathindexes(root, registry): # pragma: no cover
    # to avoid having huge pickles
    objectmap = find_objectmap(root)

    index_oids = objectmap.get_extent(get_dotted_name(PathIndex))

    for oid in index_oids:
        pathindex = objectmap.object_for(oid)
        pathindex._not_indexed = objectmap.family.IF.TreeSet(
            pathindex._not_indexed)

def includeme(config):
    config.add_evolution_step(treesetify_catalog_pathindexes)
