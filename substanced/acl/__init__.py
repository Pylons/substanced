from pyramid.security import (
    Deny,
    Everyone,
    ALL_PERMISSIONS,
    )

NO_INHERIT = (Deny, Everyone, ALL_PERMISSIONS) # API

def scan(config): # pragma: no cover
    config.scan('.views')
    
includeme = scan
