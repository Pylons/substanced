from pyramid.threadlocal import get_current_registry

def add_lock_service(registry, root):
    if 'locks' not in root:
        registry = get_current_registry()
        locks = registry.content.create('Lock Service')
        root.add_service('locks', locks, registry=registry)
    locks = root['locks']
    locks.__sdi_deletable__ = False

def includeme(config):
    config.add_evolution_step(
        add_lock_service,
        after='substanced.audit.evolve.add_root_auditlog',
        )
