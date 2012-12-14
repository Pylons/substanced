import threading

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

class AddAction(Action):

    position = 2

    def __init__(self, index, docid, obj):
        self.index = index
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
    
    def __init__(self, index, docid, obj):
        self.index = index
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
    
    def __init__(self, index, docid):
        self.index = index
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

        Entries in the chart above indicate special cases.  Typically
        the last action encountered wins, except for these cases.
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

