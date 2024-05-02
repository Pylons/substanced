from ..util import get_oid

def oid_from_resource(resource):
    oid = get_oid(resource, None)
    if not isinstance(oid, int):
        raise ValueError(
            'Resource must be an object with an integer __oid__ attribute'
            )
    return oid
