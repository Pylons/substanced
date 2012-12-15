import collections
import threading
import time
import transaction

from ZODB.POSException import ConflictError

from pyramid.threadlocal import get_current_registry

from substanced.interfaces import IIndexingActionProcessor

# MODE_ sentinels are classes so that when one is unpickled, the result can
# be compared against an imported version using "is"

class MODE_IMMEDIATE(object):
    pass

class MODE_ATCOMMIT(object):
    pass

class MODE_DEFERRED(object):
    pass

class Action(object):
    def __repr__(self):
        klass = self.__class__
        classname = '%s.%s' % (klass.__module__, klass.__name__)
        return '<%s object docid %r at %#x>' % (classname,
                                                self.docid,
                                                id(self))

class DumberNDirtActionProcessor(object):
    def __init__(self, index):
        self.index = index

    def get_root(self):
        zodb_root = self.index._p_jar.root()
        return zodb_root

    def get_queue(self):
        zodb_root = self.get_root()
        queue = zodb_root.get('dndqueue')
        return queue

    def active(self):
        return self.get_queue() is not None

    def engage(self):
        self.sync()
        queue = self.get_queue()
        if queue is None:
            zodb_root = self.get_root()
            queue = collections.deque()
            zodb_root['dndqueue'] = queue
            transaction.commit()

    def disengage(self):
        self.sync()
        zodb_root = self.get_root()
        zodb_root.pop('dndqueue')
        transaction.commit()

    def add(self, actions):
        queue = self.get_queue()
        if queue is None:
            raise RuntimeError('Queue processor not engaged')
        queue.extend(actions)

    def sync(self):
        self.index._p_jar.sync()

    def process(self, sleep=5, once=False):
        queue = self.get_queue()
        self.engage()
        try:
            while True:
                print 'doing processing'
                self.sync()
                executed = False
                while queue:
                    action = queue.popleft()
                    print 'executing %s' % (action,)
                    action.execute()
                    executed = True
                if executed:
                    try:
                        print 'committing'
                        transaction.commit()
                    except ConflictError:
                        transaction.abort()
                else:
                    print 'no actions to execute'
                if once:
                    break
                time.sleep(sleep)
        finally:
            self.disengage()

class AddAction(Action):

    position = 2

    def __init__(self, index, mode, docid, obj):
        self.index = index
        self.mode = mode
        self.docid = docid
        self.obj = obj

    def execute(self):
        self.index.index_doc(self.docid, self.obj)
        # break all refs
        self.index = None
        self.docid = None
        self.obj = None

class ChangeAction(Action):

    position = 1
    
    def __init__(self, index, mode, docid, obj):
        self.index = index
        self.mode = mode
        self.docid = docid
        self.obj = obj

    def execute(self):
        self.index.reindex_doc(self.docid, self.obj)
        # break all refs
        self.index = None
        self.docid = None
        self.obj = None

class RemoveAction(Action):

    position = 0
    
    def __init__(self, index, mode, docid):
        self.index = index
        self.mode = mode
        self.docid = docid

    def execute(self):
        self.index.unindex_doc(self.docid)
        # break all refs
        self.index = None
        self.docid = None

class IndexActionQueue(threading.local):
    def __init__(self, index):
        self.clear()
        self.index = index

    def clear(self):
        self.actions = []
        self.index = None

    def add(self, action):
        self.actions.append(action)

    def process(self):
        try:
            if self.actions:
                self.optimize()
                self._process()
        finally:
            if self.index is not None: # might have been called manually
                self.index.clear_action_queue() # suicide
            self.clear() # break any circrefs, clear out actions

    def _process(self):
        registry = get_current_registry()
        processor = registry.queryAdapter(self.index, IIndexingActionProcessor)
        processor_active = processor is not None and processor.active()
        if processor_active:
            deferred = []
            for action in self.actions:
                if action.mode is MODE_DEFERRED:
                    deferred.append(action)
                else:
                    action.execute()
            if deferred:
                processor.add(deferred)
        else:
            # if we don't have an active action processor process all of our
            # actions immediately
            for action in self.actions:
                action.execute()

    def optimize(self):
        """
        State chart for optimization.  If the new action is X and the existing
        action is Y, generate the resulting action named in the chart cells.
        
                                New    ADD      REMOVE     CHANGE
                                
           Existing     ADD            add      nothing*   add*

                      REMOVE           change*  remove     change

                      CHANGE           add      remove     change

        Starred entries in the chart above indicate special cases.  Typically
        the last action encountered in the queue is the most optimal action,
        except for the starred cases.
        """
        result = {}

        def donothing(docid, action1, action2):
            del result[docid]

        def doadd(docid, action1, action2):
            result[docid] = action1

        def dochange(docid, action1, action2):
            result[docid] = ChangeAction(action2.index, docid, action2.obj)

        def dodefault(docid, action1, action2):
            result[docid] = action2
            
        statefuncs = {
            # txn asked to remove an object that previously it was
            # asked to add, conclusion is to do nothing
            (AddAction, RemoveAction):donothing,
            # txn asked to change an object that was not previously added,
            # concusion is to just do the add
            (AddAction, ChangeAction):doadd,
            # txn action asked to remove an object then readd the same
            # object.  We translate this to a single change action.
            (RemoveAction, AddAction):dochange,
            }

        for newaction in self.actions:
            docid = newaction.docid
            oldaction = result.get(docid)
            statefunc = statefuncs.get(
                (oldaction.__class__, newaction.__class__),
                dodefault,
                )
            statefunc(docid, oldaction, newaction)

        def sorter(action):
            return (action.position, action.docid)
         
        result = list(sorted(result.values(), key=sorter))

        self.actions = result

