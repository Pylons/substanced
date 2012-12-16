import logging
import persistent
import threading
import time
import transaction

from transaction.interfaces import ISavepointDataManager

from zope.interface import implementer

from ZODB.POSException import ConflictError

from pyramid.threadlocal import get_current_registry

from substanced.interfaces import (
    IIndexingActionProcessor,
    MODE_DEFERRED,
    )

logger = logging.getLogger(__name__)

class Action(object):
    def __repr__(self):
        klass = self.__class__
        classname = '%s.%s' % (klass.__module__, klass.__name__)
        return '<%s object oid %r for index %r at %#x>' % (
            classname,
            self.oid,
            getattr(self.index, '__name__', None),
            id(self)
            )

class IndexAction(Action):

    position = 2

    def __init__(self, index, mode, oid, obj):
        self.index = index
        self.mode = mode
        self.oid = oid
        self.obj = obj

    def execute(self):
        self.index.index_doc(self.oid, self.obj)
        # break all refs
        self.index = None
        self.oid = None
        self.obj = None

class ReindexAction(Action):

    position = 1
    
    def __init__(self, index, mode, oid, obj):
        self.index = index
        self.mode = mode
        self.oid = oid
        self.obj = obj

    def execute(self):
        self.index.reindex_doc(self.oid, self.obj)
        # break all refs
        self.index = None
        self.oid = None
        self.obj = None

class UnindexAction(Action):

    position = 0
    
    def __init__(self, index, mode, oid):
        self.index = index
        self.mode = mode
        self.oid = oid

    def execute(self):
        self.index.unindex_doc(self.oid)
        # break all refs
        self.index = None
        self.oid = None

class ActionsQueue(persistent.Persistent):
    def __init__(self):
        self.actions = []

    def extend(self, actions):
        self.actions.extend(actions)
        self._p_changed = True

    def popall(self):
        if not self.actions:
            return None
        actions = self.actions[:]
        self.actions = []
        return actions

    def _p_resolveConflict(self, old_state, committed_state, new_state):
        for k, v in new_state.items():
            if k != 'actions':
                if committed_state.get(k) != v:
                    # cant cope with a conflict for anything except 'actions'
                    raise ConflictError

        committed_actions = committed_state['actions']
        new_actions = new_state['actions']
        all_actions = committed_actions + new_actions
        committed_state['actions'] = all_actions
        logger.debug('resolved %s conflict' % self.__class__.__name__)
        return committed_state

class DumberNDirtActionProcessor(object):
    def __init__(self, context):
        self.context = context

    def get_root(self):
        jar = self.context._p_jar
        if jar is None:
            return None
        zodb_root = jar.root()
        return zodb_root

    def get_queue(self):
        zodb_root = self.get_root()
        if zodb_root is None:
            return None
        queue = zodb_root.get('dndqueue')
        return queue

    def active(self):
        return self.get_queue() is not None

    def engage(self):
        self.sync()
        queue = self.get_queue()
        if queue is None:
            zodb_root = self.get_root()
            if zodb_root is None:
                raise RuntimeError('Context has no jar')
            queue = ActionsQueue()
            zodb_root['dndqueue'] = queue
            transaction.commit()

    def disengage(self):
        self.sync()
        zodb_root = self.get_root()
        if zodb_root is None:
            raise RuntimeError('Context has no jar')
        zodb_root.pop('dndqueue', None)
        transaction.commit()

    def add(self, actions):
        queue = self.get_queue()
        if queue is None:
            raise RuntimeError('Queue processor not engaged')
        queue.extend(actions)

    def sync(self):
        jar = self.context._p_jar
        if jar is not None:
            jar.sync()

    def process(self, sleep=5, once=False):
        logger.debug('engaging')
        self.engage()
        try:
            while True:
                logger.debug('doing processing')
                self.sync()
                executed = False
                queue = self.get_queue()
                actions = queue.popall()
                if actions is not None:
                    actions = optimize_actions(actions)
                    for action in actions:
                        logger.debug('executing %s' % (action,))
                        action.execute()
                        executed = True
                if executed:
                    try:
                        logger.debug('committing')
                        transaction.commit()
                    except ConflictError:
                        transaction.abort()
                else:
                    logger.debug('no actions to execute')
                if once:
                    break
                time.sleep(sleep)
        except KeyboardInterrupt:
            pass
        finally:
            logger.debug('disengaging')
            self.disengage()

class IndexActionSavepoint(object):
    """ Transaction savepoints  """

    def __init__(self, tm):
        self.tm = tm
        self.actions = tm.actions[:]

    def rollback(self):
        self.tm.actions = self.actions


@implementer(ISavepointDataManager)
class IndexActionTM(threading.local):
    # This is a data manager solely to provide savepoint support, we'd
    # otherwise be able to get away with just using a before commit hook to
    # call .process
    
    def __init__(self, index):
        self.index = index
        self.oid = index.__oid__
        self.registered = False
        self.actions = []

    def register(self):
        if not self.registered:
            t = transaction.get()
            t.join(self)
            t.addBeforeCommitHook(self.flush, (False,))
            self.registered = True

    def savepoint(self):
        return IndexActionSavepoint(self)

    def tpc_begin(self, t):
        pass

    def commit(self, t):
        pass

    def tpc_vote(self, t):
        pass

    def tpc_finish(self, t):
        self.registered = False
        self.actions = []
        if self.index is not None:
            self.index.clear_action_tm()
            self.index = None # break circref

    tpc_abort = abort = tpc_finish

    def sortKey(self):
        return self.oid

    def add(self, action):
        self.actions.append(action)

    def flush(self, all=True):
        if self.actions:
            actions = self.actions
            self.actions = []
            actions = optimize_actions(actions)
            self._process(actions, all=all)

    def _process(self, actions, all=True):
        registry = get_current_registry()

        logger.debug('begin index actions processing')

        if all:
            logger.debug('executing all actions immediately: "all" flag')
            execute_actions_immediately(actions)
            
        else:
            processor = registry.queryAdapter(
                self.index,
                IIndexingActionProcessor
                )
            processor_active = processor is not None and processor.active()
            if processor_active:
                logger.debug(
                    'executing deferred actions: action processor active'
                    )
                execute_actions_deferred(actions, processor)
            else:
                logger.debug(
                    'executing actions all immediately: no action processor'
                    )
                execute_actions_immediately(actions)

        logger.debug('done processing index actions')

def execute_actions_immediately(actions):
    for action in actions:
        logger.debug('executing action %r' % (action,))
        action.execute()

def execute_actions_deferred(actions, processor):
    deferred = []
    for action in actions:
        if action.mode is MODE_DEFERRED:
            logger.debug('adding deferred action %r' % (action,))
            deferred.append(action)
        else:
            logger.debug('executing action %r' % (action,))
            action.execute()
    if deferred:
        processor.add(deferred)

def optimize_actions(actions):
    """
    State chart for optimization.  If the new action is X and the existing
    action is Y, generate the resulting action named in the chart cells.

                            New    INDEX    UNINDEX   REINDEX

       Existing    INDEX           index     nothing*   index*

                 UNINDEX           reindex*  unindex    reindex

                 REINDEX           index     unindex    reindex

    Starred entries in the chart above indicate special cases.  Typically
    the last action encountered in the actions list is the most optimal
    action, except for the starred cases.
    """
    result = {}

    def donothing(oid, index_oid, action1, action2):
        del result[(oid, index_oid)]

    def doadd(oid, index_oid, action1, action2):
        result[(oid, index_oid)] = action1

    def dochange(oid, index_oid, action1, action2):
        result[(oid, index_oid)] = ReindexAction(
            action2.index, oid, action2.obj
            )

    def dodefault(oid, index_oid, action1, action2):
        result[(oid, index_oid)] = action2

    statefuncs = {
        # txn asked to remove an object that previously it was
        # asked to add, conclusion is to do nothing
        (IndexAction, UnindexAction):donothing,
        # txn asked to change an object that was not previously added,
        # concusion is to just do the add
        (IndexAction, ReindexAction):doadd,
        # txn action asked to remove an object then readd the same
        # object.  We translate this to a single change action.
        (UnindexAction, IndexAction):dochange,
        }

    for newaction in actions:
        oid = newaction.oid
        index_oid = newaction.index.__oid__
        oldaction = result.get((oid, index_oid))
        statefunc = statefuncs.get(
            (oldaction.__class__, newaction.__class__),
            dodefault,
            )
        statefunc(oid, index_oid, oldaction, newaction)

    def sorter(action):
        return (action.oid, action.index.__oid__, action.position)

    result = list(sorted(result.values(), key=sorter))
    return result

