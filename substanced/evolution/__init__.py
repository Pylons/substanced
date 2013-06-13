from pkg_resources import EntryPoint

from pyramid.util import (
    TopologicalSorter,
    FIRST,
    LAST,
    )

from ..interfaces import IEvolutionSteps
from BTrees import family64

_marker = object()

class EvolutionManager(object):
    def __init__(self, context, registry, txn=_marker):
        self.context = context
        self.registry = registry
        if txn is _marker:
            import transaction
            self.transaction = transaction
        else:
            self.transaction = txn

    def get_zodb_root(self):
        return self.context._p_jar.root()

    def get_finished_steps(self):
        zodb_root = self.get_zodb_root()
        finished_steps = zodb_root.setdefault(
            'substanced.finished_evolution_steps',
            family64.OO.Set()
            )
        return finished_steps

    def add_finished_step(self, name):
        finished_steps = self.get_finished_steps()
        finished_steps.insert(name)

    def remove_finished_step(self, name):
        finished_steps = self.get_finished_steps()
        finished_steps.remove(name)

    def get_unfinished_steps(self):
        tsorter = self.registry.queryUtility(IEvolutionSteps, None)
        results = []
        if tsorter is not None:
            topo_ordered = [ x[1] for x in tsorter.sorted() ]
            finished_steps = self.get_finished_steps()
            for name, func in topo_ordered:
                if not name in finished_steps:
                    results.append((name, func))
        return results

    def evolve(self, commit=True):
        steps = self.get_unfinished_steps()
        complete = []
        for name, func in steps:
            if self.transaction is not None and commit:
                self.transaction.begin()
            func(self.context)
            self.add_finished_step(name)
            if self.transaction is not None and commit:
                self.transaction.commit()
            complete.append(name)
        return complete

def add_evolution_step(config, func, before=None, after=None, name=None):
    if name is None:
        name = func.__module__ + '.' + func.__name__
    tsorter = config.registry.queryUtility(IEvolutionSteps)
    if tsorter is None:
        tsorter = TopologicalSorter(default_after=FIRST, default_before=LAST)
        config.registry.registerUtility(tsorter, IEvolutionSteps)
    tsorter.add(
        name,
        (name, func),
        before=before,
        after=after,
        )

def legacy_to_new(root):
    zodb_root = root._p_jar.root()
    finished_steps = zodb_root.setdefault(
        'substanced.finished_evolution_steps',
        family64.OO.Set()
        )
    for i in range(1, 11):
        finished_steps.insert('substanced.evolution.evolve%s.evolve' % i)

VERSION = 10         # legacy
NAME = 'substanced'  # legacy

def includeme(config): # pragma: no cover
    from .legacy import add_evolution_package
    config.add_directive('add_evolution_step', add_evolution_step)
    config.add_directive('add_evolution_package', add_evolution_package)
    config.add_evolution_package('substanced.evolution')
    config.add_evolution_step(legacy_to_new)
    for i in range(1, 11):
        scriptname = 'substanced.evolution.evolve%s' % i
        evmodule = EntryPoint.parse('x=%s' % scriptname).load(False)
        config.add_evolution_step(evmodule.evolve)
