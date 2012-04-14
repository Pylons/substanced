from repoze.evolution import (
    IEvolutionManager,
    ZODBEvolutionManager,
    )

def add_evolution_package(config, package_name):
    """ Add a package to the evolution manager.  The package should contain
    eveolveN.py scripts which evolve the database (see the
    ``repoze.evolution`` package).  Call via
    ``config.add_evolution_package``."""
    config.registry.registerUtility(ZODBEvolutionManager, IEvolutionManager, 
                                    name=package_name)

def includeme(config): #pragma: no cover
    config.add_directive('add_evolution_package', add_evolution_package)
