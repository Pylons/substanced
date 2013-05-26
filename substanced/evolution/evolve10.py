import logging

logger = logging.getLogger('evolution')

def evolve(root):
    logger.info(
        'substanced evolve step 10: add created index'
    )
    catalog = root['catalogs']['system']
    catalog.update_indexes()
    catalog.reindex(indexes=('created',))
