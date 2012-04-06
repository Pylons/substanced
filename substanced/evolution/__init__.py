from repoze.evolution import (
    IEvolutionManager,
    ZODBEvolutionManager,
    )

def add_evolution_package(config, package_name):
    config.registry.registerUtility(ZODBEvolutionManager, IEvolutionManager, 
                                    name='kuiuecomm.evolution')

def includeme(config): #pragma: no cover
    config.add_directive('add_evolution_package', add_evolution_package)
