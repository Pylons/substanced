from zope.interface import alsoProvides

from ..interfaces import IService
from ..interfaces import MODE_IMMEDIATE
from substanced.util import (
    get_acl,
    postorder,
    )
from substanced._compat import u

from logging import getLogger

_SLASH = u('/')

logger = getLogger(__name__)

def convert_services_to_IService(root):
    # can't use find_catalog because we changed it to expect IService, which
    # we are in the process of bootstrapping.
    catalog = root['catalogs']['system']
    index = catalog['interfaces']
    for val in root.values():
        try:
            del val.__is_service__
        except AttributeError:
            pass
        else:
            alsoProvides(val, IService)
            index.reindex_resource(val, action_mode=MODE_IMMEDIATE)

def add_path_to_acl_to_objectmap(root):
    objectmap = root.__objectmap__
    objectmap.path_to_acl = objectmap.family.OO.BTree()
    logger.log('Populating path_to_acl in objectmap (expensive evolve step)')
    for obj in postorder(root):
        oid = objectmap.objectid_for(obj)
        path = objectmap.path_for(oid)
        upath = _SLASH.join(path)
        acl = get_acl(obj, None)
        suffix = '(no acl)'
        if acl is not None:
            objectmap.set_acl(obj, acl)
            suffix = '(indexed acl)'
        logger.log('%s %s' (upath, suffix))

def includeme(config):
    config.add_evolution_step(convert_services_to_IService)
    config.add_evolution_step(add_path_to_acl_to_objectmap)
