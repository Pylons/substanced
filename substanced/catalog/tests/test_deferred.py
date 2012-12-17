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
        ap = DummyActionProcessor(None)
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
        ap = DummyActionProcessor(
            None, [ConflictError, ConflictError, ConflictError]
            )
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
        ap = DummyActionProcessor(
            None,
            [ConflictError, ConflictError]
            )
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

class TestIndexActionSavepoint(unittest.TestCase):
    def _makeOne(self, tm):
        from ..deferred import IndexActionSavepoint
        return IndexActionSavepoint(tm)

    def test_rollback(self):
        tm = DummyIndexActionTM([1])
        inst = self._makeOne(tm)
        tm.actions = None
        inst.rollback()
        self.assertEqual(tm.actions, [1])

class TestIndexActionTM(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, index):
        from ..deferred import IndexActionTM
        return IndexActionTM(index)

    def test_register(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        transaction = DummyTransaction()
        inst.transaction = transaction
        inst.register()
        self.assertTrue(transaction.joined)
        self.assertEqual(transaction.beforecommit_fn, inst.flush)
        self.assertEqual(transaction.beforecommit_args, (False,))
        self.assertTrue(inst.registered)

    def test_register_already_registered(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        transaction = DummyTransaction()
        inst.transaction = transaction
        inst.registered = True
        inst.register()
        self.assertFalse(transaction.joined)

    def test_savepoint(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        sp = inst.savepoint()
        self.assertEqual(sp.tm, inst)

    def test_tpc_begin(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        self.assertEqual(inst.tpc_begin(None), None)

    def test_tpc_finish(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        self.assertEqual(inst.tpc_finish(None), None)
        self.assertTrue(index.cleared)
        self.assertEqual(inst.index, None)
        self.assertFalse(inst.registered)
        self.assertEqual(inst.actions, [])

    def test_sortKey(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        self.assertEqual(inst.sortKey(), 1)

    def test_add(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        inst.add(1)
        self.assertEqual(inst.actions, [1])

    def test_flush(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        a1 = DummyAction(1)
        inst.actions = [a1]
        L = []
        inst._process = lambda actions, all=None: L.append((actions, all))
        inst.flush(all=False)
        self.assertEqual(L, [([a1], False)])

    def test_flush_no_actions(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        L = []
        inst._process = lambda actions, all=None: L.append((actions, all))
        inst.flush(all=False)
        self.assertEqual(L, [])

    def test__process_all_True(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        logger = DummyLogger()
        inst.logger = logger
        a1 = DummyAction(1)
        inst._process([a1])
        self.assertTrue(a1.executed)
        self.assertEqual(
            logger.messages,
            ['begin index actions processing',
             'executing all actions immediately: "all" flag',
             'executing action action 1',
             'done processing index actions']
            )

    def test__process_all_False_no_action_processor(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        logger = DummyLogger()
        inst.logger = logger
        a1 = DummyAction(1)
        inst._process([a1], all=False)
        self.assertTrue(a1.executed)
        self.assertEqual(
            logger.messages,
            ['begin index actions processing',
             'executing actions all immediately: no action processor',
             'executing action action 1',
             'done processing index actions']
            )

    def test__process_all_False_inactive_action_processor(self):
        from substanced.interfaces import IIndexingActionProcessor
        from zope.interface import Interface
        self.config.registry.registerAdapter(
            DummyActionProcessor, (Interface,), IIndexingActionProcessor
            )
        index = DummyIndex()
        index.active = False
        inst = self._makeOne(index)
        logger = DummyLogger()
        inst.logger = logger
        a1 = DummyAction(1)
        inst._process([a1], all=False)
        self.assertTrue(a1.executed)
        self.assertEqual(
            logger.messages,
            ['begin index actions processing',
             'executing actions all immediately: inactive action processor',
             'executing action action 1',
             'done processing index actions']
            )

    def test__process_all_False_active_action_processor(self):
        from substanced.interfaces import (
            IIndexingActionProcessor,
            MODE_DEFERRED,
            MODE_ATCOMMIT,
            )
        from zope.interface import Interface
        self.config.registry.registerAdapter(
            DummyActionProcessor, (Interface,), IIndexingActionProcessor
            )
        index = DummyIndex()
        index.active = True
        inst = self._makeOne(index)
        logger = DummyLogger()
        inst.logger = logger
        a1 = DummyAction(1)
        a1.mode = MODE_DEFERRED
        a2 = DummyAction(2)
        a2.mode = MODE_ATCOMMIT
        inst._process([a1, a2], all=False)
        self.assertFalse(a1.executed)
        self.assertTrue(a2.executed)
        self.assertEqual(index.added, [a1])
        self.assertEqual(
            logger.messages,
            ['begin index actions processing',
             'executing deferred actions: action processor active',
             'adding deferred action action 1',
             'executing action action 2',
             'done processing index actions']
            )

class Test_optimize_actions(unittest.TestCase):
    def _callFUT(self, actions):
        from ..deferred import optimize_actions
        return optimize_actions(actions)

    def test_donothing(self):
        from ..deferred import IndexAction, UnindexAction
        index = DummyIndex()
        actions = [ IndexAction(index, 'mode', 'oid', 'resource'),
                    UnindexAction(index, 'mode', 'oid') ]
        result = self._callFUT(actions)
        self.assertEqual(result, [])

    def test_doadd(self):
        from ..deferred import IndexAction, ReindexAction
        index = DummyIndex()
        actions = [ IndexAction(index, 'mode', 'oid', 'resource'),
                    ReindexAction(index, 'mode', 'oid', 'resource') ]
        result = self._callFUT(actions)
        self.assertEqual(result, [actions[0]])

    def test_dochange(self):
        from ..deferred import IndexAction, UnindexAction, ReindexAction
        index = DummyIndex()
        actions = [ UnindexAction(index, 'mode', 'oid'),
                    IndexAction(index, 'mode', 'oid', 'resource') ]
        result = self._callFUT(actions)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].__class__, ReindexAction)
        self.assertEqual(result[0].index, index)
        self.assertEqual(result[0].oid, 'oid')
        self.assertEqual(result[0].resource, 'resource')

    def test_dodefault(self):
        from ..deferred import IndexAction
        index = DummyIndex()
        actions = [ IndexAction(index, 'mode', 'oid', 'resource'),
                    IndexAction(index, 'mode', 'oid', 'resource') ]
        result = self._callFUT(actions)
        self.assertEqual(result, [actions[-1]])

    def test_sorting(self):
        from ..deferred import IndexAction, ReindexAction, UnindexAction
        index1 = DummyIndex()
        index1.__name__ = 'index1'
        index2 = DummyIndex()
        index2.__oid__ = 2
        index2.__name__ = 'index2'
        a1 = IndexAction(index2, 'mode', 'oid1', 'resource')
        a2 = ReindexAction(index1, 'mode', 'oid3', 'resource')
        a3 = IndexAction(index2, 'mode', 'oid2', 'resource')
        a4 = IndexAction(index2, 'mode', 'oid3', 'resource')
        a5 = UnindexAction(index1, 'mode', 'oid1')
        actions = [a1, a2, a3, a4, a5]
        result = self._callFUT(actions)
        self.assertEqual(result, [a5, a1, a3, a2, a4])

class DummyIndexActionTM(object):
    def __init__(self, actions):
        self.actions = actions

class DummyIndex(object):
    __oid__ = 1
    cleared = False
    def index_doc(self, oid, resource):
        self.oid = oid
        self.resource = resource

    reindex_doc = index_doc

    def unindex_doc(self, oid):
        self.oid = oid

    def clear_action_tm(self):
        self.cleared = True

class DummyLogger(object):
    def __init__(self):
        self.messages = []
    def info(self, msg):
        self.messages.append(msg)
    debug = info
        

class DummyJar(object):
    def __init__(self, result):
        self.result = result

    def root(self):
        return self.result

    def sync(self):
        self.synced = True


class DummyTransaction(object):
    joined = False
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

    def get(self):
        return self

    def join(self, tm):
        self.joined = tm

    def addBeforeCommitHook(self, fn, args):
        self.beforecommit_fn = fn
        self.beforecommit_args = args

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
    def __init__(self, context, commit_raises=None):
        self.context = context
        if commit_raises is None:
            commit_raises = []
        self.transaction = DummyTransaction(commit_raises)
        self.synced = 0
        self.called = 0

    def active(self):
        return self.context.active

    def sync(self):
        self.synced+=1

    def add(self, actions):
        self.context.added = actions

    
