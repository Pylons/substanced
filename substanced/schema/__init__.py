import colander
import deform.widget

from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('substanced')

class CSRFToken(colander.SchemaNode):

    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    
    def validator(self, node, value):
        request = self.bindings['request']
        token = request.session.get_csrf_token()
        if value != token:
            raise colander.Invalid(
                node,
                _('Invalid cross-site scripting token'),
                value
                )

    def after_bind(self, node, kw):
        token = kw['request'].session.get_csrf_token()
        self.default = token
        
class RemoveCSRFMapping(colander.Mapping):
    def deserialize(self, node, cstruct):
        result = colander.Mapping.deserialize(self, node, cstruct)
        if result is colander.null:
            return result
        result.pop('_csrf_token_', None)
        return result
                   
class Schema(colander.Schema):
    """
    A ``colander.Schema`` subclass which generates and validates a CSRF token
    automatically.  You must use it like so:

    .. code-block:: python

      from substanced.schema import Schema
      import colander

      class MySchema(Schema):
          my_value = colander.SchemaNode(colander.String())

      And in your application code, *bind* the schema, passing the request
      as a keyword argument:

      .. code-block:: python

        def aview(request):
            schema = MySchema().bind(request=request)

      In order for the CRSFSchema to work, you must configure a *session
      factory* in your Pyramid application.  This is usually done by
      Substance D itself, but may not be done for you in extremely custom
      configurations.
    """
    schema_type = RemoveCSRFMapping
    _csrf_token_ = CSRFToken()

class NameSchemaNode(colander.SchemaNode):
    """ Convenience Colander schemanode used to represent the name (aka
    ``__name__``) of an object in a propertysheet or add form which allows for
    customizing the detection of whether editing or adding is being done, and
    setting a max length for the name.

    By default it uses the context's ``check_name`` API to ensure that the name
    provided is valid, and limits filename length to a default of 100
    characters.  Some usage examples follow.
    
    This sets up the name_node to assume that it's in 'add' mode with the
    default 100 character max limit.::

      name_node = NameSchemaNode()

    This sets up the name_node to assume that it's in 'add' mode, and that the
    maximum length of the name provided is 20 characters::
    
      name_node = NameSchemaNode(max_len=20)

    This sets up the name_node to assume that it's in 'edit'
    mode (``check_name`` will be called on the **parent** of the bind
    context, not on the context itself)::
    
      name_node = NameSchemaNode(editing=True)

    This sets up the name_node to condition whether it's in edit mode on the
    result of a function::

      def i_am_editing(context, request):
          return request.registry.content.istype(context, 'Document')
    
      name_node = NameSchemaNode(editing=i_am_editing)
    """

    schema_type = colander.String
    max_len = 100
    editing = None

    def validator(self, node, value):
        context = self.bindings['context']
        request = self.bindings['request']
        editing = self.editing
        # By default, we are adding, meaning that we're checking the name
        # against the raw context which is assumed to be the parent
        # object that we're being added to.
        if editing is not None:
            if callable(editing):
                editing = editing(context, request)
            if editing:
                # However, if this is true, we are editing, not adding, which
                # means the raw context is the object itself, so we need to
                # walk up its parent chain to get the folder to call
                # ``check_name`` against.
                context = context.__parent__
        try:
            context.check_name(value)
        except Exception as e:
            raise colander.Invalid(node, e.args[0], value)
        if len(value) > self.max_len:
            raise colander.Invalid(
                node,
                'Length of name must be %s characters or fewer' % self.max_len,
                value
                )

