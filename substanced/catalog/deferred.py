import functools
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

from ..objectmap import find_objectmap
from ..util import get_oid

logger = logging.getLogger(__name__)

# functools.total_ordering allows us to define __eq__ and __lt__ and it takes
# care of the rest of the rich comparison methods (2.7+ only)

@functools.total_ordering
class Action(object):

    oid = None
    index = None
    index_oid = None
    position = None

    def __repr__(self):
        klass = self.__class__
        classname = '%s.%s' % (klass.__module__, klass.__name__)
        return '<%s object oid %r for index %r at %#x>' % (
            classname,
            self.oid,
            getattr(self.index, '__name__', self.index),
            id(self)
            )

    def __hash__(self):
        return hash((self.oid, self.index_oid))

    def __eq__(self, other):
        # Note that we don't take our class or position into account because
        # we want to compare equal to any other action that has the same
        # oid for the same index.
        return (self.oid, self.index_oid) == (other.oid, other.index_oid)

    def __lt__(self, other):
        # Note that during sorting we *do* take our position into account.
        self_cmp = (self.oid, self.index_oid, self.position)
        other_cmp = (other.oid, other.index_oid, other.position)
        return self_cmp < other_cmp

    def find_resource(self):
        objectmap = find_objectmap(self.index)
        resource = objectmap.object_for(self.oid)
        if resource is None:
            raise ResourceNotFound(self.oid)
        return resource

class ResourceNotFound(Exception):
    def __init__(self, oid):
        self.oid = oid

    def __repr__(self):
        return 'Indexing error: cannot find resource for oid %s' % self.oid

class IndexAction(Action):

    position = 2

    def __init__(self, index, mode, oid, index_oid=None):
        self.index = index
        if index_oid is None:
            index_oid = get_oid(index)
        self.index_oid = index_oid
        self.mode = mode
        self.oid = oid

    def execute(self):
        resource = self.find_resource()
        self.index.index_doc(self.oid, resource)

    def anti(self):
        return UnindexAction(self.index, self.mode, self.oid, self.index_oid)

class ReindexAction(Action):

    position = 1
    
    def __init__(self, index, mode, oid, index_oid=None):
        self.index = index
        if index_oid is None:
            index_oid = get_oid(index)
        self.index_oid = index_oid
        self.mode = mode
        self.oid = oid

    def execute(self):
        resource = self.find_resource()
        self.index.reindex_doc(self.oid, resource)

    def anti(self):
        return self

class UnindexAction(Action):

    position = 0
    
    def __init__(self, index, mode, oid, index_oid=None):
        self.index = index
        if index_oid is None:
            index_oid = get_oid(index)
        self.index_oid = index_oid
        self.mode = mode
        self.oid = oid

    def execute(self):
        self.index.unindex_doc(self.oid)

    def anti(self):
        return IndexAction(self.index, self.mode, self.oid, self.index_oid)

class ActionsQueue(persistent.Persistent):

    logger = logger # for testing

    def __init__(self):
        self.undo = False # will be True in states resulting from an undo
        self.gen = 0
        self.actions = []
        self.pactive = False

    def bumpgen(self):
        # At an average rate of 100 bumps per second, this value won't exceed
        # sys.maxint for:
        #
        # About 8 months on a 32-bit system.
        #
        # About 92 years on a 64-bit system.
        #
        # The software will work fine after it exceeds sys.maxint, it'll
        # overflow to a long integer and it'll just be slower to do the math to
        # bump.
        #
        # I choose to not care about the slowdown that overflowing to a long
        # integer on incredibly busy 32-bit systems will imply.  32-bit systems
        # will have a real chance of getting slower over time as this integer
        # continually increases and its long integer representation uses more
        # bits as it does.  If someone uses this software 100 years from now,
        # and they're still using a 64 bit CPU, they'll also need to deal with
        # the slowdown implied by overflowing to a long integer too, but that's
        # obviously not too concerning.
        #
        # It's possible to reset this value to 0 periodically.  Resetting this
        # value to 0 should only be done immediately after a pack.  It is only
        # used to compare old object revisions to newer ones, and after a pack,
        # there are no old object revisions anymore.  It would be ideal to be
        # able to hook into the pack process to do this automatically, but
        # there aren't really any hooks for it.
        self.undo = False
        self.gen = self.gen + 1

    def extend(self, actions):
        self.actions.extend(actions)
        self.bumpgen()
        self._p_changed = True

    def popall(self):
        if not self.actions:
            return None
        actions = self.actions[:]
        self.actions = []
        self.bumpgen()
        return actions

    def _p_resolveConflict(self, old_state, committed_state, new_state):
        self.logger.info(
            'Running _p_resolveConflict for %s' % self.__class__.__name__
            )

        # We only know how to merge actions and resolve the generation and undo
        # flag.  If anything else is different, puke.
        if set(new_state.keys()) != set(committed_state.keys()):
            raise ConflictError

        for key, val in new_state.items():
            if ( key not in ('actions', 'gen', 'undo') and
                 val != committed_state[key] ):
                raise ConflictError

        # we need to get rid of duplicate actions to make actions merging
        # possible; optimize_states mutates the actions in the states so that
        # each list has exactly one and only one action per oid+index
        # combination
        optimize_states(old_state, committed_state, new_state)

        # A good bit of this code was cadged from zc.queue._queue
        old = old_state['actions']
        committed = committed_state['actions']
        new = new_state['actions']
        
        old_set = set(old)
        committed_set = set(committed)
        new_set = set(new)

        committed_added = committed_set - old_set
        committed_removed = old_set - committed_set

        new_added = new_set - old_set
        new_removed = old_set - new_set

        # At this point we know which (oid,index) identifiers should be added
        # to the old state and which should be removed: the union of
        # new_removed and committed_removed should be removed, and the union of
        # new_added and committed_added should be added.  But if there are
        # individual actions within the removed or added sets that compare
        # equal, the actions are keyed in the set only by (oid,index) and their
        # __eq__ doesn't take into account the action type.  For example, there
        # might be two different actions which compare equal in the different
        # sets: a reindex action for oid 1 in the new_removed set and an
        # unindex action for the same oid in the committed_removed set.
        #
        # The 'action_union' function will return a union of two sets composed
        # of actions.  When two actions in the sets compare otherwise equal it
        # will return the "real" action or it will conflict for two actions
        # that compare equal but which are mutually incompatible.  For example,
        # if we have an index action for oid 1 in new_removed, and a reindex
        # action for oid 1 in committed_removed, the index action will be
        # returned (the reindex action will be discarded).  There is no
        # conflict in this case. On the other hand, the action_union function
        # might raise a ConflictError if it can't determine what to do; an
        # example of a case where action_union wouldn't know what to do is if
        # there's an index action for oid 1 in new_removed, and an unindex
        # action for oid 1 in committed_removed.

        removed = action_union(new_removed, committed_removed)
        assert(removed == new_removed|committed_removed) # chris' sanity

        added = action_union(new_added, committed_added)
        assert(added == new_added|committed_added) # chris' sanity

        # The union of the old actions and the added actions represents
        # something we can subtract our removed actions from.

        union = action_union(old_set, added)
        # chris' sanity
        assert(union == old_set|added)

        result = union - removed
        # chris' sanity
        assert(result == (old_set|added) - (new_removed|committed_removed))

        # If the new state's generation number is less than the old state's
        # generation number, we know we're in the process of undoing a
        # transaction that involved the queue.  This is because during an undo
        # the "new_state" state is the state of the queue in the transaction
        # prior to the undone transaction (the state that would have been
        # rolled back to if this conflict did not occur), and the "old_state"
        # is actually the state of the transaction we're trying to undo.
        undoing = (old_state['gen'] > new_state['gen'])

        if undoing:
            self.logger.info(
                'generating anti-actions during undo in %s '
                '_p_resolveConflict' % (
                    self.__class__.__name__
                    )
                )
            # During an undo the "new_state" state is the state of the queue in
            # the transaction prior to the undone transaction (the state that
            # we're rolling back to), and the "old_state" is actually the state
            # of the transaction we're trying to undo.

            # While we're undoing, it's not enough to just omit the removed
            # actions from the returned action state, as we do in the non-undo
            # case.  Instead we need to add anti-actions for every action in
            # the state that we're undoing.  For example, if we determine via
            # that an UnindexAction was in the old state, we'll need to add an
            # IndexAction to the returned state in order to get the object into
            # the indexed state eventually (when the queue processor runs).  If
            # there was an IndexAction, we need to add an UnindexAction, etc.

            # Some inspiration from this undo logic comes from staring at
            # Products.QueueCatalog
            result.update([action.anti() for action in removed])
            committed_state['undo'] = True
            gen = committed_state['gen'] + 1
        else:
            gen = max(committed_state['gen'], new_state['gen'])

        # NB: ordering doesn't make a damn bit of difference because the
        # actions we already optimized and it is impossible to have more than
        # one action per (oid,index) in the result, but we sort here for test
        # sanity.
        result = list(sorted(result))

        committed_state['actions'] = result
        committed_state['gen'] = gen

        self.logger.info(
            'resolved %s conflict in _p_resolveConflict' % (
                self.__class__.__name__
                )
            )

        return committed_state

def commit(tries):
    def wrapper(wrapped):
        def retry(self, *arg, **kw):
            for _ in range(tries):
                self.sync()
                self.transaction.begin()
                try:
                    result = wrapped(self, *arg, **kw)
                    self.transaction.commit()
                    return result
                except ConflictError:
                    self.transaction.abort()
            raise ConflictError
        return retry
    return wrapper

class Break(Exception):
    pass

class BasicActionProcessor(object):

    logger = logger # for testing
    transaction = transaction # for testing
    queue_name = 'basic_action_queue'
    
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
        queue = zodb_root.get(self.queue_name)
        return queue

    def active(self):
        queue = self.get_queue()
        if queue is None:
            return False
        return queue.pactive

    def sync(self):
        jar = self.context._p_jar
        if jar is not None:
            jar.sync()

    @commit(5)
    def engage(self):
        queue = self.get_queue()
        if queue is None:
            zodb_root = self.get_root()
            if zodb_root is None:
                raise RuntimeError('Context has no jar')
            queue = ActionsQueue()
            queue.pactive = True
            zodb_root[self.queue_name] = queue
        else:
            queue.pactive = True

    @commit(1)
    def disengage(self):
        queue = self.get_queue()
        if queue is not None:
            queue.pactive = False

    def add(self, actions):
        queue = self.get_queue()
        if queue is None:
            raise RuntimeError('Queue processor not engaged')
        queue.extend(actions)

    def process(self, sleep=5, once=False):
        self.logger.info('starting basic action processor')
        self.engage()
        while True:
            try:

                if not once: # pragma: no cover
                    time.sleep(sleep)

                self.logger.info('start running actions processing')
                self.sync()
                self.transaction.begin()

                executed = False
                commit = False

                queue = self.get_queue()
                actions = queue.popall()

                if actions is not None:
                    actions = optimize_actions(actions)
                    for action in actions:
                        self.logger.info('executing %s' % (action,))
                        try:
                            executed = True
                            action.execute()
                        except ResourceNotFound as e:
                            self.logger.info(repr(e))
                        else:
                            commit = True

                if commit:
                    self.logger.info('committing')
                    try:
                        self.transaction.commit()
                        self.logger.info('committed')
                    except ConflictError:
                        self.transaction.abort()
                        self.logger.info('aborted due to conflict error')

                if not executed:
                    self.logger.info('no actions to execute')
                self.logger.info('end running actions processing')

                if once:
                    raise Break()

            except (SystemExit, KeyboardInterrupt, Break):
                once = True
                try:
                    self.logger.info('stopping basic action processor')
                    self.disengage()
                    break
                except ConflictError:
                    self.logger.info(
                        'couldnt disengage due to conflict, processing queue '
                        'once more'
                        )

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

    transaction = transaction # for testing
    logger = logger # for testing
    
    def __init__(self, index):
        self.index = index
        self.oid = index.__oid__
        self.registered = False
        self.actions = []

    def register(self):
        if not self.registered:
            t = self.transaction.get()
            t.join(self)
            t.addBeforeCommitHook(self.flush, (False,))
            self.registered = True

    def savepoint(self):
        return IndexActionSavepoint(self)

    def tpc_begin(self, t):
        pass

    commit = tpc_vote = tpc_begin

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

        self.logger.debug('begin index actions processing')

        if all:
            self.logger.debug('executing all actions immediately: "all" flag')
            self.execute_actions_immediately(actions)
            
        else:
            processor = registry.queryAdapter(
                self.index,
                IIndexingActionProcessor
                )

            active = False
            reason = None

            if processor:
                active = processor.active()
                if not active:
                    reason = 'inactive'
            else:
                reason = 'no'

            if active:
                self.logger.debug(
                    'executing deferred actions: action processor active'
                    )
                self.execute_actions_deferred(actions, processor)
            else:
                self.logger.debug(
                    'executing actions all immediately: %s action '
                    'processor' % (reason,)
                    )
                self.execute_actions_immediately(actions)

        self.logger.debug('done processing index actions')

    def execute_actions_immediately(self, actions):
        for action in actions:
            self.logger.debug('executing action %r' % (action,))
            action.execute()

    def execute_actions_deferred(self, actions, processor):
        deferred = []
        for action in actions:
            if action.mode is MODE_DEFERRED:
                self.logger.debug('adding deferred action %r' % (action,))
                deferred.append(action)
            else:
                self.logger.debug('executing action %r' % (action,))
                action.execute()
        if deferred:
            processor.add(deferred)

def action_union(s1, s2):
    """ Call which_action for each action in s1 that has an analogue in s2 to
    determine which of two actions that operate against the same oid+index
    should be preferred.  If neither is preferred, a ConflictError will be
    raised."""
    union = s1 | s2
    L1 = [ ( (a.oid, a.index_oid), a) for a in s1 ]
    L2 = [ ( (a.oid, a.index_oid), a) for a in s2 ]
    ds1 = dict(L1)
    ds2 = dict(L2)
    for k1, action1 in ds1.items():
        action2 = ds2.get(k1)
        if action2 is not None:
            # replace action in union with correct one or conflict
            union.add(which_action(action1, action2))
    return union

def which_action(a1, a2):
    """
    Compare two actions and return 'the right' one, or raise a ConflictError.
    It's presumed that both actions share the same (oid,index).  We use this
    state chart to determine what is returned:

                             A1    INDEX      UNINDEX     REINDEX

       A2          INDEX           index      conflict*   index*

                 UNINDEX           conflict*  unindex     conflict*

                 REINDEX           index*     conflict*   reindex
    """
    def doconflict(a1, a2):
        raise ConflictError
    def dosecond(a1, a2):
        return a2
    def dofirst(a1, a2):
        return a1
    statefuncs = {
        (IndexAction, UnindexAction):doconflict,
        (UnindexAction, IndexAction):doconflict,
        (ReindexAction, UnindexAction):doconflict,
        (UnindexAction, ReindexAction):doconflict,
        (ReindexAction, IndexAction):dosecond,
        }
    return statefuncs.get((a1.__class__, a2.__class__), dofirst)(a1, a2)

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
            action2.index, action2.mode, oid,
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
        index_oid = newaction.index_oid
        oldaction = result.get((oid, index_oid))
        statefunc = statefuncs.get(
            (oldaction.__class__, newaction.__class__),
            dodefault,
            )
        statefunc(oid, index_oid, oldaction, newaction)

    result = list(sorted(result.values()))
    return result

def optimize_states(old_state, committed_state, new_state):
    """ Optimize actions in states during conflict resolution """
    old = old_state['actions']
    committed = committed_state['actions']
    new = new_state['actions']

    old, new, committed = map(optimize_actions, [old, new, committed])

    old_state['actions'] = old
    committed_state['actions'] = committed
    new_state['actions'] = new

