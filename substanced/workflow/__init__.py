from collections import defaultdict

from pyramid.config import ConfigurationError
from pyramid.security import has_permission
from pyramid.threadlocal import get_current_registry
from zope.interface import implementer

from persistent.mapping import PersistentMapping

from ..interfaces import (
    IWorkflow,
    IDefaultWorkflow,
    )
from ..content import get_content_type
from ..event import subscribe_added


STATE_ATTR = '__workflow_state__'

class WorkflowError(Exception):
    """Exception raised for anything related to :mod:`substanced.workflow`.
    """

@implementer(IWorkflow)
class Workflow(object):
    """Finite state machine.

    Implements `substanced.interfaces.IWorkflow`.

    :param initial_state: Initial state of the workflow assigned to the content
    :type initial_state: string

    :param type: Identifier to separate multiple workflows on same content.
    :type type: string

    :param name: Display name.
    :type name: string

    :param description: Not used internally, provided as help text to describe
                        what workflow does.
    :type description: string
    """
    _state_factory = dict       # overridable by instances / subclasses
    _transition_factory = dict  # overridable by instances / subclasses

    def __init__(self, initial_state, type, name='', description=''):
        self._transitions = {}
        self._states = {}
        self._initial_state = initial_state
        self.type = type
        self.name = name
        self.description = description

    def add_state(self, state_name, callback=None, **kw):
        """Add a new workflow state.

        :param state_name: Unique name of the state for this workflow.
        :param callback: Will be called when content enters this state.
                         Meaning :meth:`Workflow.reset`,
                         :meth:`Workflow.initialize`,
                         :meth:`Workflow.transition` and
                         :meth:`Workflow.transition_to_state` will trigger
                         callback if entering this state.
        :type callback: callable
        :param \*\*kw: Metadata assigned to this state.

        :raises: :exc:`WorkflowError` if state already exists.

        Callback is called with **content** as first argument and **meta**
        as second. **meta** is a dictionary containing **workflow**,
        **transition** and **request**. Be aware that methods as
        :meth:`Workflow.initialize` pass **transition** as empty dictionary.

        .. note::
            ``**kw`` must not contain the key
            ``callback``. This name is reserved for internal use.
        """
        if state_name in self._states:
            raise WorkflowError('State %s already defined' % state_name)
        kw['callback'] = callback
        self._states[state_name] = self._state_factory(**kw)

    def add_transition(self, transition_name, from_state, to_state,
                       callback=None, permission=None, **kw):
        """Add a new workflow transition.

        :param transition_name: Unique name of transition for this workflow.
        :param callback: Will be called when transition is executed.
                         Meaning :meth:`Workflow.transition` and
                         :meth:`Workflow.transition_to_state` will trigger
                         callback if this transition is executed.
        :type callback: callable
        :param \*\*kw: Metadata assigned to this state.

        :raises: :exc:`WorkflowError` if transition already exists.
        :raises: :exc:`WorkflowError` if from_state or to_state don't exist.

        Callback is called with **content** as first argument and **meta**
        as second. **meta** is a dictionary containing **workflow**,
        **transition** and **request**.

        .. note::
            ``**kw`` must not contain any of the keys ``from_state``, ``name``,
            ``to_state``, or ``callback``; these are reserved for internal use.

        """
        if transition_name in self._transitions:
            raise WorkflowError(
                'Duplicate transition name %s' % transition_name)
        if from_state not in self._states:
            raise WorkflowError('No such state %r' % from_state)
        if to_state not in self._states:
            raise WorkflowError('No such state %r' % to_state)
        transition = self._transition_factory(
                                name=transition_name,
                                from_state=from_state,
                                to_state=to_state,
                                callback=callback,
                                permission=permission,
                                **kw)
        self._transitions[transition_name] = transition

    def check(self):
        """Check the consistency of the workflow state machine.

        :raises: :exc:`WorkflowError` if workflow is inconsistent.

        """
        if self._initial_state not in self._states:
            raise WorkflowError('Workflow must define its initial state %r'
                                % self._initial_state)

    def _set_state(self, content, state, request, transition=None):
        if transition is None:
            transition = {}
        states = getattr(content, STATE_ATTR, None)
        if not states:
            states = PersistentMapping()
            setattr(content, STATE_ATTR, states)
        msg = None
        new_state = self._states[state]
        callback = getattr(new_state, '__call__', None)
        if callback is None:
            callback = self._states[state].get('callback')
        if callback is not None:
            msg = callback(content,
                           request=request,
                           transition=transition,
                           workflow=self,
                          )
        states[self.type] = state
        return state, msg

    def state_of(self, content):
        """Return the current state of the content object or None
        if the content object does not have this workflow.
        """
        states = getattr(content, STATE_ATTR, None)
        if states:
            return states.get(self.type, None)

    def has_state(self, content):
        """Return True if the content has state for this workflow,
        False if not.
        """
        return self.state_of(content) is not None

    def _get_states(self, content, from_state=None):
        content_state = self.state_of(content)
        if from_state is None:
            from_state = content_state

        L = []

        for state_name, state in self._states.items():
            D = {'name': state_name, 'transitions': []}
            D['data'] = state
            D['initial'] = state_name == self._initial_state
            D['current'] = state_name == content_state
            D['title'] = state.get('title', state_name)
            for tname, transition in self._transitions.items():
                if (transition['from_state'] == from_state and
                        transition['to_state'] == state_name):
                    transitions = D['transitions']
                    transitions.append(transition)
            L.append(D)

        return L

    def get_states(self, content, request, from_state=None):
        """Return all states for the workflow.

        :param content: Object to be operated on
        :param request: `pyramid.request.Request` instance
        :param from_state: State of the content. If None,
                           :meth:`Workflow.state_of` will be used on
                           **content**.

        :rtype: list of dicts
        :returns: Where dictionary contains information about the transition,
                  such as **title**, **initial**, **current**,
                  **transitions** and **data**. **transitions** is return value
                  of :meth:`Workflow.get_transitions` call for current state.
                  **data** is a dictionary containing at least **callback**.

        .. note::
            States that fail `has_permission` check for their transition
            are left out.

        """
        states = self._get_states(content, from_state)
        for state in states:
            L = []
            for transition in state['transitions']:
                permission = transition.get('permission')
                if permission is not None:
                    if not has_permission(permission, content,
                                          request):
                        continue
                L.append(transition)
            state['transitions'] = L
        return states

    def initialize(self, content, request=None):
        """Initialize the content object to the initial state of this workflow.

        :param content: Object to be operated on
        :param request: `pyramid.request.Request` instance
        :returns: (initial_state, msg)

        `msg` is a string returned by the state `callback`.

        """
        state, msg = self._set_state(content, self._initial_state, request)
        return self._initial_state, msg

    def reset(self, content, request=None):
        """Reset the content workflow by calling the callback of
        it's current state and setting its state attr.

        If content has no current state, it will be initialized
        for this workflow (see initialize).

        `msg` is a string returned by the state callback.

        :param content: Object to be operated on
        :param request: `pyramid.request.Request` instance
        :returns: (state, msg)

        """
        state = self.state_of(content)
        if state is None:
            return self.initialize(content)
        try:
            stateinfo = self._states[state]
        except KeyError:
            raise WorkflowError('No such state %s for workflow %s' %
                                (state, self.name))
        state, msg = self._set_state(content, state, request)
        return state, msg

    def _transition(self, content, transition_name, context=None,
                    request=None):
        if context is None:
            context = content

        state = self.state_of(content)

        si = (state, transition_name)

        transition = None
        for tname, candidate in self._transitions.items():
            match = (candidate['from_state'], candidate['name'])
            if si == match:
                transition = candidate
                break

        if transition is None:
            raise WorkflowError(
                'No transition from state %r using transition name %r'
                % (state, transition_name))

        permission = transition.get('permission')
        if permission is not None:
            if not has_permission(permission, context, request):
                raise WorkflowError(
                    '%s permission required for transition using %r' % (
                    permission, self.name)
                    )

        from_state = transition['from_state']
        to_state = transition['to_state']

        info = {
            'workflow': self,
            'transition': transition,
            'request': request,
        }

        callback = getattr(transition, '__call__', None)
        if callback is None:
            callback = transition.get('callback')
        if callback is not None:
            callback(content,
                     request=request,
                     transition=transition,
                     workflow=self,
                    )

        self._set_state(content, to_state, request, transition)

    def transition(self, content, request, transition_name):
        """Execute a transition using a **transition_name** on **content**.

        :param content: Object to be operated on.
        :param request: `pyramid.request.Request` instance
        :param transition_name: Name of transition to execute.

        :raises: :exc:`WorkflowError` if no transition is found
        :raises: :exc:`WorkflowError` if transition doesn't pass
                                      `has_permission` check
        """
        self._transition(content, transition_name, request=request)

    def _transition_to_state(self, content, to_state, context=None,
                             request=None, skip_same=True):
        from_state = self.state_of(content)
        if (from_state == to_state) and skip_same:
            return
        states = self._get_states(content)
        for info in states:
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

    def transition_to_state(self, content, request, to_state,
                            skip_same=True):
        """Execute a transition to another state using a state name
        (**to_state**). All possible transitions towards **to_state**
        will be tried until one if found that passes without exception.

        :param content: Object to be operated on.
        :param request: `pyramid.request.Request` instance
        :param to_state: State to transition to.
        :param skip_same: If True and the **to_state** is the same as
                          the content state, no transition is issued.

        :raises: :exc:`WorkflowError` if no transition is found

        """
        self._transition_to_state(content, to_state,
                                  request=request, skip_same=skip_same)

    def _get_transitions(self, content, from_state=None):
        if from_state is None:
            from_state = self.state_of(content)

        transitions = []
        for tname, transition in self._transitions.items():
            if from_state == transition['from_state']:
                transitions.append(transition)

        return transitions

    def get_transitions(self, content, request, from_state=None):
        """Get all transitions from the content state.

        :param content: Object to be operated on.
        :param request: `pyramid.request.Request` instance
        :param from_state: Name of the state to retrieve transitions. If None,
                           :meth:`Workflow.state_of` will be used on
                           **content**.
        :rtype: list of dicts
        :returns: Where dictionary contains information about the transition,
                  such as **from_state**, **to_state**, **callback**,
                  **permission** and **name**.

        .. note::
            Transitions that fail `has_permission` check are left out.

        """
        transitions = self._get_transitions(content, from_state)
        L = []
        for transition in transitions:
            permission = transition.get('permission')
            if permission is not None:
                if not has_permission(permission, content,
                                      request):
                    continue
            L.append(transition)
        return L

def get_workflow(request, type, content_type=None):
    """Return a workflow based on a content_type and the workflow type.

    :param request: `pyramid.request.Request` instance
    :param type: Workflow type
    :param content_type: Substanced content type or None for default workflow.

    """
    if content_type is None:
        content_type = IDefaultWorkflow

    reg = request.registry
    return reg.workflow.get(type, content_type)

def register_workflow(config, workflow, type_,
                      content_type=None):
    if content_type is None:
        content_type = IDefaultWorkflow

    reg = config.registry
    if not reg.content.exists(content_type):
        raise ConfigurationError('Workflow %s registered for content_type %s '
                                 'which does not exist.' % (workflow,
                                                            content_type))

    reg.workflow.add(workflow, content_type)

def add_workflow(config, workflow, content_types=(None,)):
    """Configurator method for adding a workflow.

    If no **content_types** is given, workflow is registered globally.

    :param config: Pyramid configurator
    :param workflow: :class:`Workflow` instance
    :param content_types: Register workflow for given content_types
    :type content_types: iterable

    :raises: :exc:`ConfigurationError` if :meth:`Workflow.check` fails
    :raises: :exc:`ConfigurationError` if **content_type** does not exist
    :raises: :exc:`DoesNotImplement` if **workflow** does not
             implement IWorkflow
    """
    if not IWorkflow.providedBy(workflow):
        raise ValueError('Not a workflow')

    try:
        workflow.check()
    except WorkflowError, why:
        raise ConfigurationError(str(why))

    intr = config.introspectable(
        'substance d workflows',
        (IWorkflow, content_types, workflow.type),
        content_types,
        'substance d workflow',
        )
    intr['workflow'] = workflow
    intr['type'] = workflow.type
    intr['content_types'] = content_types

    for content_type in content_types:
        config.action((IWorkflow, content_type, workflow.type),
                      callable=register_workflow,
                      introspectables=(intr,),
                      order=9999,
                      args=(config, workflow, workflow.type, content_type))

@subscribe_added()
def init_workflows_for_object(event):
    """Initialize workflows when object is added to db.
    """
    obj = event.object
    content_type = get_content_type(obj)
    registry = get_current_registry()

    if content_type is None:
        # maybe we should register workflows not relevant
        # to specific content type?
        return

    for wf in registry.workflow.get_all_types(content_type):
        wf.initialize(obj)

class WorkflowRegistry(object):

    def __init__(self):
        self.types = defaultdict(dict)
        self.content_types = defaultdict(dict)

    def add(self, wf, content_type):
        self.types[wf.type][content_type] = wf
        self.content_types[content_type][wf.type] = wf

    def get(self, type, content_type):
        type_ = self.types.get(type, None)
        if type_:
            return type_.get(content_type, type_.get(IDefaultWorkflow, None))

    def get_all_types(self, content_type):
        types = dict(self.content_types.get(IDefaultWorkflow, {}))
        types.update(dict(self.content_types.get(content_type, {})))
        return types.values()

def includeme(config): # pragma: no cover
    config.add_directive('add_workflow', add_workflow)
    config.registry.workflow = WorkflowRegistry()
