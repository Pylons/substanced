from substanced.audit import AuditLog
from substanced.util import postorder

def remove_bogus_auditlogs(root):
    i = 0
    for resource in postorder(root):
        i += 1
        if resource is not root:
            if hasattr(resource, '__auditlog__'):
                del resource.__auditlog__
        resource._p_deactivate()
        if i % 1000 == 0:
            resource._p_jar.cacheGC()

def add_root_auditlog(root):
    if not hasattr(root, '__auditlog__'):
        root.__auditlog__ = AuditLog()
        
def includeme(config):
    config.add_evolution_step(remove_bogus_auditlogs)
    config.add_evolution_step(add_root_auditlog)

