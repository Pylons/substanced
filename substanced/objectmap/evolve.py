from logging import getLogger

import BTrees

from .._compat import u
from ..util import (
    get_acl,
    postorder,
    )

_SLASH = u('/')

logger = getLogger(__name__)

def oobtreeify_referencemap(root, registry): # pragma: no cover
    objectmap = root.__objectmap__
    refmap = objectmap.referencemap.refmap
    for k, refset in refmap.items():
        refset.src2target = BTrees.family64.OO.BTree(refset.src2target)
        refset.target2src = BTrees.family64.OO.BTree(refset.target2src)

def oobtreeify_object_to_path(root, registry): # pragma: no cover
    objectmap = root.__objectmap__
    oobtree = BTrees.family64.OO.BTree
    objectmap.objectid_to_path = oobtree(objectmap.objectid_to_path)
    objectmap.path_to_objectid = oobtree(objectmap.path_to_objectid)

def treesetify_objectmap_pathindex(root, registry): # pragma: no cover
    # to avoid having huge pickles
    objectmap = root.__objectmap__
    pathindex = objectmap.pathindex
    for path, not_treesets in list(pathindex.items()):
        for d, not_treeset in list(not_treesets.items()):
            treeset = objectmap.family.IF.TreeSet(not_treeset)
            not_treesets[d] = treeset

def treesetify_referencesets(root, registry): # pragma: no cover
    # to avoid having huge pickles
    objectmap = root.__objectmap__
    refmap = objectmap.referencemap.refmap
    for name, refset in list(refmap.items()):
        for reftype, oidset in list(refset.src2target.items()):
            if oidset.__class__ != refset.oidset_class:
                refset.src2target[reftype] = refset.oidset_class(oidset)
        for reftype, oidset in list(refset.target2src.items()):
            if oidset.__class__ != refset.oidset_class:
                refset.target2src[reftype] = refset.oidset_class(oidset)

def add_path_to_acl_to_objectmap(root, registry):
    objectmap = root.__objectmap__
    objectmap.path_to_acl = objectmap.family.OO.BTree()
    logger.info('Populating path_to_acl in objectmap (expensive evolve step)')
    for obj in postorder(root):
        oid = objectmap.objectid_for(obj)
        path = objectmap.path_for(oid)
        upath = _SLASH.join(path)
        acl = get_acl(obj, None)
        suffix = '(no acl)'
        if acl is not None:
            objectmap.set_acl(obj, acl)
            suffix = '(indexed acl)'
        logger.info('%s %s' % (upath, suffix))

def includeme(config): # pragma: no cover
    config.add_evolution_step(oobtreeify_referencemap)
    config.add_evolution_step(oobtreeify_object_to_path)
    config.add_evolution_step(treesetify_objectmap_pathindex)
    config.add_evolution_step(treesetify_referencesets)
    config.add_evolution_step(add_path_to_acl_to_objectmap)
    
