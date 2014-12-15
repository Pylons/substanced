from zope.interface import alsoProvides

from ..interfaces import IService
from ..interfaces import MODE_IMMEDIATE

def convert_services_to_IService(root, registry):
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

def includeme(config):
    config.add_evolution_step(convert_services_to_IService)
