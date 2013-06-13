import transaction

from pyramid.util import TopologicalSorter

from ..interfaces import IEvolutionSteps
from ..util import get_dotted_name
from .._compat import STRING_TYPES

from BTrees import family64

_marker = object()

FINISHED_KEY = 'substanced.finished_evolution_steps'

class EvolutionManager(object):
    def __init__(self, context, registry, txn=None):
        self.context = context
        self.registry = registry
        if txn is None:
            self.transaction = transaction
        else:
            self.transaction = txn

    def get_zodb_root(self):
        return self.context._p_jar.root()

    def get_finished_steps(self):
        zodb_root = self.get_zodb_root()
        finished_steps = zodb_root.setdefault(FINISHED_KEY, family64.OO.Set())
        return finished_steps

    def add_finished_step(self, name):
        finished_steps = self.get_finished_steps()
        finished_steps.insert(name)

    def remove_finished_step(self, name):
        finished_steps = self.get_finished_steps()
        finished_steps.remove(name)

    def get_unfinished_steps(self):
        tsorter = self.registry.queryUtility(IEvolutionSteps)
        if tsorter is not None:
            topo_ordered = [ x[1] for x in tsorter.sorted() ]
            finished_steps = self.get_finished_steps()
            for name, func in topo_ordered:
                if not name in finished_steps:
                    yield name, func

    def mark_unfinshed_as_finished(self):
        finished = self.get_finished_steps()
        unfinished = self.get_unfinished_steps()
        for name, func in unfinished:
            finished.insert(name)

    def evolve(self, commit=True):
        steps = self.get_unfinished_steps()
        complete = []
        for name, func in steps:
            if commit:
                self.transaction.begin()
            self.out('Executing evolution step %s' % name)
            func(self.context)
            self.add_finished_step(name)
            if commit:
                self.transaction.note('Executed evolution step %s' % name)
                self.transaction.commit()
            complete.append(name)
        return complete

    def out(self, msg): # pragma: no cover
        print (msg)

def mark_unfinished_as_finished(app_root, registry, t=None):
    """ Given the root object of a Substance D site as ``app_root`` and a
    Pyramid registry, mark all pending evolution steps as completed without
    actually executing them."""
    emanager = EvolutionManager(app_root, registry, t)
    return emanager.mark_unfinished_as_finished()

def add_evolution_step(config, func, before=None, after=None, name=None):
    """
    A configurator directive which adds an evolution step.  An evolution step
    can be used to perform upgrades or migrations of data structures in
    existing databases to meet expectations of new code.

    ``func`` should be a function that performs the evolution logic.  It should
    accept a single argument (conventionally named) ``root``.  This will
    be the root of the main ZODB database used to serve your Substance D site.

    ``before`` should either be ``None``, another evolution step function, or
    the dotted name to such a function.  By default, it is ``None``, which
    means execute in the order defined by the calling order of
    ``add_evolution_step``.

    ``after`` should either be ``None``, another evolution step function, or
    the dotted name to such a function.  By default, it is ``None``.

    ``name`` is the name of the evolution step.  It must be unique between all
    registered evolution steps.  If it is not provided, the dotted name of
    the function used as ``func`` will be used as the evolution step name.
    """
    func_desc = config.object_description(func)
    if name is None:
        name = get_dotted_name(func)
    else:
        func_desc = func_desc + ' (%s)' % name
    if after is not None and not isinstance(after, STRING_TYPES):
        after = get_dotted_name(after)
    if before is not None and not isinstance(before, STRING_TYPES):
        before = get_dotted_name(before)
    discriminator = ('evolution step', name)
    intr = config.introspectable(
        'evolution steps', discriminator, func_desc, 'evolution step')
    intr['name'] = name
    intr['func'] = func
    intr['before'] = before
    intr['after'] = after
    def register():
        tsorter = config.registry.queryUtility(IEvolutionSteps)
        if tsorter is None:
            tsorter = TopologicalSorter()
            config.registry.registerUtility(tsorter, IEvolutionSteps)
        tsorter.add(name, (name, func), before=before, after=after)
    config.action(discriminator, register, introspectables=(intr,))

VERSION = 10         # legacy
NAME = 'substanced'  # legacy

def legacy_to_new(root): # pragma: no cover
    zodb_root = root._p_jar.root()
    last = zodb_root.get('repoze.evolution', {}).get('substanced.evolution', 1)
    finished_steps = zodb_root.setdefault(FINISHED_KEY, family64.OO.Set())
    for i in range(1, last+1):
        finished_steps.insert('substanced.evolution.evolve%s.evolve' % i)

def includeme(config): # pragma: no cover
    config.add_directive('add_evolution_step', add_evolution_step)
