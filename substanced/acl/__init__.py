from pyramid.security import (
    Deny,
    Everyone,
    ALL_PERMISSIONS,
    )

NO_INHERIT = (Deny, Everyone, ALL_PERMISSIONS) # API

def includeme(config):
    config.scan('substanced.acl.views')
    
