from substanced.util import get_oid

def assertint(oid):
    if not isinstance(oid, (int, long)):
        raise ValueError('%r is not an integer value; catalog oids must be '
                         'integers' % (oid,))

def oid_from_resource(resource, oid):
    if oid is None:
        oid = get_oid(resource, None)
        if oid is None:
            raise ValueError('resource has no oid and no oid was passed')
    assertint(oid)
    return oid

def oid_from_resource_or_oid(resource_or_oid):
    oid = get_oid(resource_or_oid, None)
    if oid is None:
        oid = resource_or_oid
    assertint(oid)
    return oid

    
