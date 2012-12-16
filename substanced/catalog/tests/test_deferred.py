import unittest
from pyramid import testing

class TestAction(unittest.TestCase):
    def _makeOne(self):
        from ..deferred import Action
        return Action()

    def test___repr__(self):
        inst = self._makeOne()
        result = repr(inst)
        self.assertTrue(
            result.startswith(
                '<substanced.catalog.deferred.Action object oid None for '
                'index None at')
            )

    def test___hash__(self):
        inst = self._makeOne()
        self.assertEqual(hash(inst), 1)

    def test___eq__True(self):
        inst = self._makeOne()
        other = self._makeOne()
        self.assertTrue(inst == other)

    def test___eq__False(self):
        inst = self._makeOne()
        other = self._makeOne()
        other.oid = 123
        self.assertFalse(inst == other)

    def test___lt__(self):
        inst = self._makeOne()
        other = self._makeOne()
        other.oid = 2
        inst.oid = 1
        self.assertTrue(inst < other)
        
    def test___gt__(self):
        # wrapped with total_ordering from functools, so this should work
        inst = self._makeOne()
        other = self._makeOne()
        other.oid = 2
        inst.oid = 1
        self.assertTrue(other.__gt__(inst))

class Test_pr_wrap(unittest.TestCase):
    def _callFUT(self, obj):
        from ..deferred import pr_wrap
        return pr_wrap(obj)

    def test_with_nonref(self):
        self.assertEqual(self._callFUT(1), 1)

    def test_with_ref(self):
        from ZODB.ConflictResolution import PersistentReference
        from ..deferred import PersistentReferenceProxy
        ref = PersistentReference((None, None))
        self.assertEqual(self._callFUT(ref).__class__, PersistentReferenceProxy)

class TestPersistentReferenceProxy(unittest.TestCase):
    def _makeOne(self, pr):
        from ..deferred import PersistentReferenceProxy
        return PersistentReferenceProxy(pr)

    def test___hash__(self):
        inst = self._makeOne(None)
        self.assertEqual(hash(inst), 1)

    def test___eq__True(self):
        inst1 = self._makeOne(None)
        inst2 = self._makeOne(None)
        self.assertTrue(inst1 == inst2)

    def test___eq__False(self):
        inst1 = self._makeOne(None)
        inst2 = self._makeOne(True)
        self.assertFalse(inst1 == inst2)

    def test___eq__raises_ValueError(self):
        class DummyPR(object):
            def __eq__(self, other):
                raise ValueError
        pr = DummyPR()
        inst1 = self._makeOne(pr)
        inst2 = self._makeOne(None)
        result = inst1 == inst2
        self.assertFalse(result)
        
    def test___ne__True(self):
        inst1 = self._makeOne(None)
        inst2 = self._makeOne(True)
        self.assertTrue(inst1 != inst2)
        
    def test___ne__False(self):
        inst1 = self._makeOne(None)
        inst2 = self._makeOne(None)
        self.assertFalse(inst1 != inst2)

class TestIndexAction(unittest.TestCase):
    def _makeOne(self, index, mode='mode', oid='oid', resource='resource'):
        from ..deferred import IndexAction
        return IndexAction(index, mode, oid, resource)

    def test_execute(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        inst.execute()
        self.assertEqual(index.oid, 'oid')
        self.assertEqual(index.resource, 'resource')
        self.assertEqual(inst.index, None)
        self.assertEqual(inst.oid, None)
        self.assertEqual(inst.resource, None)

class TestReindexAction(unittest.TestCase):
    def _makeOne(self, index, mode='mode', oid='oid', resource='resource'):
        from ..deferred import ReindexAction
        return ReindexAction(index, mode, oid, resource)

    def test_execute(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        inst.execute()
        self.assertEqual(index.oid, 'oid')
        self.assertEqual(index.resource, 'resource')
        self.assertEqual(inst.index, None)
        self.assertEqual(inst.oid, None)
        self.assertEqual(inst.resource, None)

class TestUnindexAction(unittest.TestCase):
    def _makeOne(self, index, mode='mode', oid='oid'):
        from ..deferred import UnindexAction
        return UnindexAction(index, mode, oid)

    def test_execute(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        inst.execute()
        self.assertEqual(index.oid, 'oid')
        self.assertEqual(inst.index, None)
        self.assertEqual(inst.oid, None)

class TestActionsQueue(unittest.TestCase):
    def _makeOne(self):
        from ..deferred import ActionsQueue
        return ActionsQueue()

    def test_extend(self):
        inst = self._makeOne()
        inst.extend([1])
        self.assertEqual(inst.actions, [1])
        # cant check for _p_changed getting set, some magic goes on that causes
        # it to be false, bleh

    def test_popall_no_actions(self):
        inst = self._makeOne()
        self.assertEqual(inst.popall(), None)

    def test_popall_with_actions(self):
        inst = self._makeOne()
        inst.actions = [1, 2]
        self.assertEqual(inst.popall(), [1,2])
        self.assertEqual(inst.actions, [])

    def test__p_resolveConflict_states_have_different_keys(self):
        from ZODB.POSException import ConflictError
        inst = self._makeOne()
        self.assertRaises(
            ConflictError,
            inst._p_resolveConflict, None, {'a':1}, {'b':2}
            )
        
    def test__p_resolveConflict_unknown_state_value_change(self):
        from ZODB.POSException import ConflictError
        inst = self._makeOne()
        self.assertRaises(
            ConflictError,
            inst._p_resolveConflict, None, {'a':1}, {'a':2}
            )

    def test_both_new_and_commited_removed_same(self):
        from ZODB.POSException import ConflictError
        inst = self._makeOne()
        old = {'actions':[1]}
        committed = {'actions':[]}
        new = {'actions':[]}
        self.assertRaises(
            ConflictError,
            inst._p_resolveConflict, old, committed, new
            )
        
    def test_both_new_and_commited_added_same(self):
        from ZODB.POSException import ConflictError
        inst = self._makeOne()
        old = {'actions':[]}
        committed = {'actions':[1]}
        new = {'actions':[1]}
        self.assertRaises(
            ConflictError,
            inst._p_resolveConflict, old, committed, new
            )
        
    def test_with_no_new_added(self):
        inst = self._makeOne()
        old = {'actions':[]}
        committed = {'actions':[2]}
        new = {'actions':[]}
        logger = DummyLogger()
        inst.logger = logger
        result = inst._p_resolveConflict(old, committed, new)
        self.assertEqual(len(logger.messages), 1)
        self.assertEqual(result, {'actions':[2]})

    def test_with_new_added(self):
        inst = self._makeOne()
        old = {'actions':[]}
        committed = {'actions':[2]}
        new = {'actions':[3]}
        logger = DummyLogger()
        inst.logger = logger
        result = inst._p_resolveConflict(old, committed, new)
        self.assertEqual(len(logger.messages), 1)
        self.assertEqual(result, {'actions':[2, 3]})

    def test_with_new_removed(self):
        inst = self._makeOne()
        old = {'actions':[1]}
        committed = {'actions':[1, 2]}
        new = {'actions':[]}
        logger = DummyLogger()
        inst.logger = logger
        result = inst._p_resolveConflict(old, committed, new)
        self.assertEqual(len(logger.messages), 1)
        self.assertEqual(result, {'actions':[2]})

class Test_commit(unittest.TestCase):
    def _makeOne(self, tries, meth):
        from ..deferred import commit
        return commit(tries)(meth)

    def test_gardenpath(self):
        ap = DummyActionProcessor()
        def fakemethod(ap):
            ap.called += 1
        inst = self._makeOne(3, fakemethod)
        inst(ap)
        self.assertEqual(ap.synced, 1)
        self.assertEqual(ap.called, 1)
        self.assertEqual(ap.transaction.begun, 1)
        self.assertEqual(ap.transaction.committed, 1)

    def test_conflict_overflow(self):
        from ZODB.POSException import ConflictError
        ap = DummyActionProcessor([ConflictError, ConflictError, ConflictError])
        def fakemethod(ap):
            ap.called += 1
        inst = self._makeOne(3, fakemethod)
        self.assertRaises(ConflictError, inst, ap)
        self.assertEqual(ap.synced, 3)
        self.assertEqual(ap.called, 3)
        self.assertEqual(ap.transaction.begun, 3)
        self.assertEqual(ap.transaction.committed, 0)
        self.assertEqual(ap.transaction.aborted, 3)

    def test_conflicts_but_success(self):
        from ZODB.POSException import ConflictError
        ap = DummyActionProcessor([ConflictError, ConflictError])
        def fakemethod(ap):
            ap.called += 1
        inst = self._makeOne(3, fakemethod)
        inst(ap)
        self.assertEqual(ap.synced, 3)
        self.assertEqual(ap.called, 3)
        self.assertEqual(ap.transaction.begun, 3)
        self.assertEqual(ap.transaction.committed, 1)
        self.assertEqual(ap.transaction.aborted, 2)

class TestBasicActionProcessor(unittest.TestCase):
    def _makeOne(self, context):
        from ..deferred import BasicActionProcessor
        return BasicActionProcessor(context)

    def test_get_root_no_jar(self):
        context = testing.DummyResource()
        context._p_jar = None
        inst = self._makeOne(context)
        self.assertTrue(inst.get_root() is None)

    def test_get_root_with_jar(self):
        context = testing.DummyResource()
        context._p_jar = DummyJar('root')
        inst = self._makeOne(context)
        self.assertEqual(inst.get_root(), 'root')

    def test_get_queue_no_root(self):
        context = testing.DummyResource()
        context._p_jar = None
        inst = self._makeOne(context)
        self.assertTrue(inst.get_queue() is None)
        
    def test_get_queue_with_root(self):
        context = testing.DummyResource()
        inst = self._makeOne(context)
        context._p_jar = DummyJar({inst.queue_name:'queue'})
        self.assertEqual(inst.get_queue(), 'queue')

    def test_active_True(self):
        context = testing.DummyResource()
        inst = self._makeOne(context)
        context._p_jar = DummyJar({inst.queue_name:'queue'})
        self.assertTrue(inst.active())
        
    def test_active_False(self):
        context = testing.DummyResource()
        context._p_jar = None
        inst = self._makeOne(context)
        self.assertFalse(inst.active())

    def test_engage_queue_already_exists(self):
        context = testing.DummyResource()
        inst = self._makeOne(context)
        context._p_jar = DummyJar({inst.queue_name:'queue'})
        self.assertEqual(inst.engage(), None)

    def test_engage_queue_missing_context_has_no_jar(self):
        context = testing.DummyResource()
        inst = self._makeOne(context)
        context._p_jar = DummyJar(None)
        self.assertRaises(RuntimeError, inst.engage)

    def test_engage_queue_added(self):
        context = testing.DummyResource()
        inst = self._makeOne(context)
        transaction = DummyTransaction()
        inst.transaction = transaction
        root = {}
        context._p_jar = DummyJar(root)
        self.assertEqual(inst.engage(), None)
        self.assertTrue(root[inst.queue_name])
        self.assertTrue(transaction.committed)

    def test_disengage_context_has_no_jar(self):
        context = testing.DummyResource()
        inst = self._makeOne(context)
        context._p_jar = DummyJar(None)
        self.assertRaises(RuntimeError, inst.disengage)

    def test_disengage_queue_removed(self):
        context = testing.DummyResource()
        inst = self._makeOne(context)
        root = {inst.queue_name:True}
        transaction = DummyTransaction()
        inst.transaction = transaction
        context._p_jar = DummyJar(root)
        inst.disengage()
        self.assertEqual(root, {})
        self.assertTrue(transaction.committed)

    def test_add_not_engaged(self):
        context = testing.DummyResource()
        context._p_jar = None
        inst = self._makeOne(context)
        self.assertRaises(RuntimeError, inst.add, [1])

    def test_add_extends(self):
        context = testing.DummyResource()
        inst = self._makeOne(context)
        root = {inst.queue_name:[1]}
        context._p_jar = DummyJar(root)
        inst.add([2,3])
        self.assertEqual(root[inst.queue_name], [1,2,3])

    def test_process_gardenpath(self):
        context = testing.DummyResource()
        inst = self._makeOne(context)
        transaction = DummyTransaction()
        inst.transaction = transaction
        logger = DummyLogger()
        inst.logger = logger
        a1 = DummyAction(1)
        queue = DummyQueue([a1])
        root = {inst.queue_name:queue}
        jar = DummyJar(root)
        context._p_jar = jar
        inst.process(once=True)
        self.assertTrue(jar.synced)
        self.assertEqual(queue.result, [])
        self.assertTrue(a1.executed)
        self.assertTrue(transaction.begun)
        self.assertEqual(transaction.committed, 3) # engage, process, disengage
        self.assertEqual(
            logger.messages,
            ['engaging basic action processor',
             'start running actions processing',
             'executing action 1',
             'committing',
             'committed',
             'end running actions processing',
             'disengaging basic action processor']
            )

    def test_process_gardenpath_no_actions(self):
        context = testing.DummyResource()
        inst = self._makeOne(context)
        transaction = DummyTransaction()
        inst.transaction = transaction
        logger = DummyLogger()
        inst.logger = logger
        queue = DummyQueue([])
        root = {inst.queue_name:queue}
        jar = DummyJar(root)
        context._p_jar = jar
        inst.process(once=True)
        self.assertTrue(jar.synced)
        self.assertEqual(queue.result, [])
        self.assertTrue(transaction.begun)
        self.assertEqual(transaction.committed, 2) # engage, disengage
        self.assertEqual(
            logger.messages,
            ['engaging basic action processor',
             'start running actions processing',
             'no actions to execute',
             'end running actions processing',
             'disengaging basic action processor']
            )

    def test_process_conflicterror_at_initial_commit(self):
        from ZODB.POSException import ConflictError
        context = testing.DummyResource()
        inst = self._makeOne(context)
        transaction = DummyTransaction([ConflictError])
        inst.transaction = transaction
        logger = DummyLogger()
        inst.logger = logger
        inst.engage = lambda *arg, **kw: False
        inst.disengage = lambda *arg, **kw: False
        a1 = DummyAction(1)
        queue = DummyQueue([a1])
        root = {inst.queue_name:queue}
        jar = DummyJar(root)
        context._p_jar = jar
        inst.process(once=True)
        self.assertTrue(jar.synced)
        self.assertEqual(queue.result, [])
        self.assertTrue(a1.executed)
        self.assertTrue(transaction.begun)
        self.assertTrue(transaction.aborted)
        self.assertEqual(
            logger.messages,
            ['engaging basic action processor',
             'start running actions processing',
             'executing action 1',
             'committing',
             'aborted due to conflict error',
             'end running actions processing',
             'disengaging basic action processor']
            )

    def test_process_conflicterror_at_disengage(self):
        from ZODB.POSException import ConflictError
        context = testing.DummyResource()
        inst = self._makeOne(context)
        transaction = DummyTransaction([None, ConflictError])
        inst.transaction = transaction
        logger = DummyLogger()
        inst.logger = logger
        inst.engage = lambda *arg, **kw: False
        L = [ConflictError]
        def disengage(*arg, **kw):
            if L:
                raise L.pop(0)
        inst.disengage = disengage
        a1 = DummyAction(1)
        queue = DummyQueue([a1])
        root = {inst.queue_name:queue}
        jar = DummyJar(root)
        context._p_jar = jar
        inst.process(once=True)
        self.assertTrue(jar.synced)
        self.assertEqual(queue.result, [])
        self.assertTrue(a1.executed)
        self.assertEqual(
            logger.messages,
            ['engaging basic action processor',
             'start running actions processing',
             'executing action 1',
             'committing',
             'committed',
             'end running actions processing',
             'disengaging basic action processor',
             'couldnt disengage due to conflict, process queue one more time',
             'start running actions processing',
             'no actions to execute',
             'end running actions processing',
             'disengaging basic action processor']            
            )
        

class DummyIndex(object):
    def index_doc(self, oid, resource):
        self.oid = oid
        self.resource = resource

    reindex_doc = index_doc

    def unindex_doc(self, oid):
        self.oid = oid

class DummyLogger(object):
    def __init__(self):
        self.messages = []
    def info(self, msg):
        self.messages.append(msg)
        

class DummyJar(object):
    def __init__(self, result):
        self.result = result

    def root(self):
        return self.result

    def sync(self):
        self.synced = True


class DummyTransaction(object):
    def __init__(self, raises=None):
        if raises is None:
            raises = []
        self.raises = raises
        self.committed = 0
        self.aborted = 0
        self.begun = 0

    def begin(self):
        self.begun += 1

    def commit(self):
        if self.raises:
            result = self.raises.pop(0)
            if result is not None:
                raise result
        self.committed += 1

    def abort(self):
        self.aborted += 1

class DummyAction(object):
    index = testing.DummyResource()
    index.__oid__ = 1
    executed = False

    def __init__(self, oid):
        self.oid = oid

    def execute(self):
        self.executed = True

    def __repr__(self):
        return 'action %s' % self.oid

class DummyQueue(object):
    def __init__(self, result):
        self.result = result
    def popall(self):
        result = self.result[:]
        self.result = []
        return result

class DummyActionProcessor(object):
    def __init__(self, commit_raises=None):
        if commit_raises is None:
            commit_raises = []
        self.transaction = DummyTransaction(commit_raises)
        self.synced = 0
        self.called = 0

    def sync(self):
        self.synced+=1

    
