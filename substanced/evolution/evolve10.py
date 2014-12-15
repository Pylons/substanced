import logging

logger = logging.getLogger('evolution')

def evolve(root, registry):
    logger.info(
        'substanced evolve step 10: add created index'
    )
    catalog = root['catalogs']['system']
    catalog.update_indexes()
    if catalog.get('created'):
        catalog.reindex(indexes=('created',))
