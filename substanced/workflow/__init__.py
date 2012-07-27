from pyramid.config import ConfigurationError
from pyramid.security import has_permission
from pyramid.threadlocal import get_current_registry
from zope.interface import (
    implements,
    providedBy,
    classImplements,
    )
from zope.interface.interfaces import IInterface
from zope.interface.verify import verifyObject

from ..interfaces import (
    IWorkflow,
    IWorkflowFactory,
    IWorkflowList,
    IDefaultWorkflow,
    ICallbackInfo,
    )


STATE_ATTR = '__workflow_state__'

class WorkflowError(Exception):
    """"""

class Workflow(object):
    """Finite state machine.
    """
    classImplements(IWorkflowFactory)
    implements(IWorkflow)

    def __init__(self, initial_state, type, name='', description=''):
        self.type = type
        self._transition_data = {}
        self._transition_order = []
        self._state_data = {}
        self._state_order = []
        self.initial_state = initial_state
        self.name = name
        self.description = description

    def __call__(self, context):
        return self # allow ourselves to act as an adapter

    def add_state(self, state_name, callback=None, **kw):
        """Add a state to the FSM.  ``**kw`` must not contain the key
        ``callback``.  This name is reserved for internal use.
        """
        if state_name in self._state_order:
            raise WorkflowError('State %s already defined' % state_name)
        kw['callback'] = callback
        self._state_data[state_name] = kw
        self._state_order.append(state_name)

    def add_transition(self, transition_name, from_state, to_state,
                       callback=None, permission=None, **kw):
        """Add a transition to the FSM.  ``**kw`` must not contain
        any of the keys ``from_state``, ``name``, ``to_state``, or
        ``callback``; these are reserved for internal use.
        """
        if transition_name in self._transition_order:
            raise WorkflowError(
                'Duplicate transition name %s' % transition_name)
        if not from_state in self._state_order:
            raise WorkflowError('No such state %r' % from_state)
        if not to_state in self._state_order:
            raise WorkflowError('No such state %r' % to_state)
        transition = kw
        transition['name'] = transition_name
        transition['from_state'] = from_state
        transition['to_state'] = to_state
        transition['callback'] = callback
        transition['permission'] = permission
        self._transition_data[transition_name] = transition
        self._transition_order.append(transition_name)

    def check(self):
        """"""
        if not self.initial_state in self._state_order:
            raise WorkflowError('Workflow must define its initial state %r'
                                % self.initial_state)

    def _state_of(self, content):
        states = getattr(content, STATE_ATTR, None)
        if states:
            return states.get(self.type, None)

    def _set_state(self, content, state):
        states = getattr(content, STATE_ATTR, None)
        if not states:
            setattr(content, STATE_ATTR, {})
        getattr(content, STATE_ATTR)[self.type] = state

    def state_of(self, content):
        """"""
        if content is None: # for add forms
            return self.initial_state
        state = self._state_of(content)
        if state is None:
            state, msg = self.initialize(content)
        return state

    def has_state(self, content):
        """"""
        return self._state_of(content) is not None

    def _state_info(self, content, from_state=None):
        content_state = self.state_of(content)
        if from_state is None:
            from_state = content_state

        L = []

        for state_name in self._state_order:
            D = {'name': state_name, 'transitions': []}
            state_data = self._state_data[state_name]
            D['data'] = state_data
            D['initial'] = state_name == self.initial_state
            D['current'] = state_name == content_state
            title = state_data.get('title', state_name)
            D['title'] = title
            for tname in self._transition_order:
                transition = self._transition_data[tname]
                if (transition['from_state'] == from_state and
                        transition['to_state'] == state_name):
                    transitions = D['transitions']
                    transitions.append(transition)
            L.append(D)

        return L

    def state_info(self, content, request, context=None, from_state=None):
        """"""
        if context is None:
            context = content
        states = self._state_info(content, from_state)
        for state in states:
            L = []
            for transition in state['transitions']:
                permission = transition.get('permission')
                if permission is not None:
                    if not has_permission(permission, context,
                                          request):
                        continue
                L.append(transition)
            state['transitions'] = L
        return states

    def initialize(self, content, request=None):
        """"""
        callback = self._state_data[self.initial_state]['callback']
        msg = None
        if callback is not None:
            info = CallbackInfo(self, {}, request)
            msg = callback(content, info)
        self._set_state(content, self.initial_state)
        return self.initial_state, msg

    def reset(self, content, request=None):
        """"""
        state = self._state_of(content)
        if state is None:
            state, msg = self.initialize(content)
            return self.initial_state, msg
        try:
            stateinfo = self._state_data[state]
        except KeyError:
            raise WorkflowError('No such state %s for workflow %s' %
                                (state, self.name))
        callback = stateinfo['callback']
        msg = None
        if callback is not None:
            info = CallbackInfo(self, {}, request)
            msg = callback(content, info)
        self._set_state(content, state)
        return state, msg

    def _transition(self, content, transition_name, context=None,
                    request=None):
        """ Execute a transition via a transition name """
        if context is None:
            context = content

        state = self.state_of(content)

        si = (state, transition_name)

        transition = None
        for tname in self._transition_order:
            t = self._transition_data[tname]
            match = (t['from_state'], t['name'])
            if si == match:
                transition = t
                break

        if transition is None:
            raise WorkflowError(
                'No transition from %r using transition name %r'
                % (state, transition_name))

        info = CallbackInfo(self, transition, request=request)

        permission = info.transition.get('permission')
        if permission is not None:
            if not has_permission(permission, context, request):
                raise WorkflowError(
                    '%s permission required for transition using %r' % (
                    permission, self.name)
                    )

        from_state = transition['from_state']
        to_state = transition['to_state']

        transition_callback = transition['callback']
        if transition_callback is not None:
            transition_callback(content, info)

        state_callback = self._state_data[to_state]['callback']
        if state_callback is not None:
            state_callback(content, info)

        self._set_state(content, to_state)

    def transition(self, content, request, transition_name, context=None):
        """"""
        self._transition(content, transition_name, context=context,
                         request=request)

    def _transition_to_state(self, content, to_state, context=None,
                             request=None, skip_same=True):
        from_state = self.state_of(content)
        if (from_state == to_state) and skip_same:
            return
        state_info = self._state_info(content)
        for info in state_info:
            if info['name'] == to_state:
                transitions = info['transitions']
                if transitions:
                    for transition in transitions:
                        try:
                            return self._transition(
                                content, transition['name'],
                                context, request)
                        except WorkflowError, e:
                            exc = e
                    raise exc
        raise WorkflowError(
            'No transition from state %r to state %r' % (from_state, to_state))

    def transition_to_state(self, content, request, to_state, context=None,
                            skip_same=True):
        """"""
        self._transition_to_state(content, to_state, context,
                                  request=request, skip_same=skip_same)

    def _get_transitions(self, content, from_state=None):
        if from_state is None:
            from_state = self.state_of(content)

        transitions = []
        for tname in self._transition_order:
            transition = self._transition_data[tname]
            if from_state == transition['from_state']:
                transitions.append(transition)

        return transitions

    def get_transitions(self, content, request, context=None, from_state=None):
        """"""
        if context is None:
            context = content
        transitions = self._get_transitions(content, from_state)
        L = []
        for transition in transitions:
            permission = transition.get('permission')
            if permission is not None:
                if not has_permission(permission, context,
                                      request):
                    continue
            L.append(transition)
        return L

class CallbackInfo(object):
    implements(ICallbackInfo)

    def __init__(self, workflow, transition, request=None):
        self.workflow = workflow
        self.transition = transition
        self.request = request

def get_workflow(request, type, content_type=IDefaultWorkflow):
    """Return a workflow based on a content_type, the workflow type.
    """
    reg = request.registry

    # TODO: work with substanced content_types strings
    if not IInterface.providedBy(content_type):
        content_type = providedBy(content_type)

    if content_type not in (None, IDefaultWorkflow):
        wf_list = reg.adapters.lookup((content_type,),
                                      IWorkflowList,
                                      name=type,
                                      default=None)
        if wf_list:
            return wf_list[0]

    wf_list = reg.adapters.lookup((IDefaultWorkflow,),
                                  IWorkflowList,
                                  name=type,
                                  default=None)
    if wf_list:
        return wf_list[0]

def register_workflow(config, workflow, type_,
                      content_type=IDefaultWorkflow):
    """"""

    # TODO: initialize workflow on content types
    # TODO: introduce substanced content_types
    if not IInterface.providedBy(content_type):
        content_type = providedBy(content_type)

    reg = config.registry

    # check for existing workflow and if none exist, register it
    wf_list = reg.adapters.lookup((content_type,),
                                  IWorkflowList,
                                  name=type_,
                                  default=None)

    if wf_list is None:
        reg.registerAdapter(workflow,
                            (content_type,),
                            IWorkflowList,
                            type_)

def add_workflow(config, workflow, content_types=(None,)):
    """"""

    verifyObject(IWorkflow, workflow)

    try:
        workflow.check()
    except WorkflowError, why:
        raise ConfigurationError(str(why))

    for content_type in content_types:
        config.action((IWorkflow, content_type, workflow.type),
                      callable=register_workflow,
                      args=(config, workflow, workflow.type, content_type))

def includeme(config): # pragma: no cover
    config.add_directive('add_workflow', add_workflow)
