from substanced.util import (
    get_oid,
    is_folder,
    )
    
import logging

_marker = object()

logger = logging.getLogger('evolution')

def postorder(startnode):
    """ Cannot use utils.postorder because it uses node.values """
    def visit(node):
        if is_folder(node):
            for child in node.data.values():
                for result in visit(child):
                    yield result
        yield node
    return visit(startnode)

def evolve(root):
    logger.info(
        'Running substanced evolve step 8: add explicit oid ordering to folders'
        )
    for obj in postorder(root):
        if is_folder(obj):
            logger.info(
                'Substanced evolve step 8: trying %s' % (obj,)
                )
            order = getattr(obj, '_order', None)
            if order is not None:
                import pdb; pdb.set_trace()
                oid_order = ()
                name_order = ()
                if order:
                    if len(order[0]) == 2:
                        # handle ree-ordering-clientside-foo-bar-baz branch
                        name_order = tuple([x[0] for x in order])
                        oid_order = tuple([x[1] for x in order])
                    else:
                        # handle master branch
                        name_order = obj._order
                        oid_order = []
                        for name in name_order:
                            oid_order.append(get_oid(obj.data[name]))
                obj._order = name_order
                obj._order_oids = oid_order
