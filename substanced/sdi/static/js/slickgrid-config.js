
(function ($) {

    // our custom validator
    function requiredFieldValidator(value) {
        if (value === null || value === undefined || !value.length) {
            return {valid: false, msg: "This is a required field"};
        } else {
            return {valid: true, msg: null};
        }
    }

    // mapping of all the default options that configure the behavior
    // of the grid. If your workflow is to marshall the options
    // from the server encoded as JSON, then this is the place where
    // you can specify those options that contain non-JSON marshallable
    // objects (such as, functions).
    // This data will be looked up from the node where the grid is bound
    // to, and its parent nodes. This allows for multiple configurations
    // inside a project.
    $(document).data('slickgrid-config', {
        editors: {
            //text: Slick.Editors.Text,
            //date: Slick.Editors.Date
        },
        formatters: {
        },
        validators: {
            //required: requiredFieldValidator
        }
      //,  handleCreate: function() {
            // Finish customizing the grid.
            // The following objects are available:
            //
            // this.grid:         the grid
            // this.dataView:     the data or data view
            // this.columns:      column definitions
            // this.origColumns:  column definitions saved
            // this.element:      the element which binds the grid
        //}

    });
})(window.jQuery);

