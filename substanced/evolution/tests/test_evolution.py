import unittest

class TestEvolutionManager(unittest.TestCase):
    def _makeOne(self, context, registry, txn):
        from .. import EvolutionManager
        return EvolutionManager(context, registry, txn)

    def test_ctor_real_txn_module(self):
        import transaction
        inst = self._makeOne(None, None, None)
        self.assertEqual(inst.transaction, transaction)

    def test_ctor_provided_txn_module(self):
        txn = DummyTransaction()
        inst = self._makeOne(None, None, txn)
        self.assertEqual(inst.transaction, txn)

    def test_get_zodb_root(self):
        root = DummyRoot()
        inst = self._makeOne(root, None, None)
        zodb_root = inst.get_zodb_root()
        self.assertEqual(zodb_root, root._p_jar._root)

    def test_get_finished_steps(self):
        from .. import FINISHED_KEY
        root = DummyRoot()
        inst = self._makeOne(root, None, None)
        steps = inst.get_finished_steps()
        self.assertEqual(steps, root._p_jar._root[FINISHED_KEY])

    def test_add_finished_step(self):
        from .. import FINISHED_KEY
        root = DummyRoot()
        inst = self._makeOne(root, None, None)
        inst.add_finished_step('foo')
        steps = root._p_jar._root[FINISHED_KEY]
        self.assertTrue('foo' in steps)

    def test_remove_finished_step(self):
        root = DummyRoot()
        inst = self._makeOne(root, None, None)
        steps = inst.get_finished_steps()
        steps.insert('foo')
        inst.remove_finished_step('foo')
        self.assertFalse('foo' in steps)

    def test_get_unifinished_steps_no_utility(self):
        registry = DummyRegistry(None)
        inst = self._makeOne(None, registry, None)
        result = inst.get_unfinished_steps()
        self.assertEqual(list(result), [])
        
    def test_get_unifinished_steps(self):
        steps = DummySteps(
            [(None, ('foo', None)),
             (None, ('bar', None))]
            )
        root = DummyRoot()
        registry = DummyRegistry(steps)
        inst = self._makeOne(root, registry, None)
        finished = inst.get_finished_steps()
        finished.insert('foo')
        result = inst.get_unfinished_steps()
        self.assertEqual(list(result), [('bar', None)])

    def test_evolve_commit_false(self):
        root = DummyRoot()
        txn = DummyTransaction()
        inst = self._makeOne(root, None, txn)
        def func(context):
            self.assertEqual(context, root)
        inst.get_unfinished_steps = lambda *arg: [('name', func)]
        log = []
        inst.out = log.append
        result = inst.evolve(False)
        self.assertEqual(log, ['Executing evolution step name'])
        self.assertEqual(result, ['name'])
        self.assertEqual(txn.committed, 0)
        self.assertEqual(txn.begun, 0)
        self.assertEqual(txn.notes, [])

    def test_evolve_commit_true(self):
        root = DummyRoot()
        txn = DummyTransaction()
        inst = self._makeOne(root, None, txn)
        def func(context):
            self.assertEqual(context, root)
        inst.get_unfinished_steps = lambda *arg: [('name', func)]
        log = []
        inst.out = log.append
        result = inst.evolve(True)
        self.assertEqual(log, ['Executing evolution step name'])
        self.assertEqual(result, ['name'])
        self.assertEqual(txn.committed, 1)
        self.assertEqual(txn.begun, 1)
        self.assertEqual(txn.notes, ['Executed evolution step name'])

class DummyTransaction(object):
    def __init__(self):
        self.begun = 0
        self.committed = 0
        self.notes = []

    def begin(self):
        self.begun += 1

    def commit(self):
        self.committed += 1

    def note(self, msg):
        self.notes.append(msg)

class DummyJar(object):
    def __init__(self):
        self._root = {}
    def root(self):
        return self._root

class DummyRoot(object):
    def __init__(self):
        self._p_jar = DummyJar()
        
class DummyRegistry(object):
    def __init__(self, utility):
        self.utility = utility

    def queryUtility(self, iface):
        return self.utility

class DummySteps(object):
    def __init__(self, result):
        self.result = result

    def sorted(self):
        return self.result
