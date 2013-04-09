
(function ($) {

    "use strict"; // jshint ;_;

    function findDefaultOptions(element, options) {
        // Fetch the configuration if we have any.
        // We walk up the DOM from element, and use 
        // the first existing data attribute with the key configName.
        // This will serve as default options, that overrides
        // the static defaults defined by this class.
        var configName = options.configName;
        var config;
        if (configName) {
            var $el = element;
            while ($el.length > 0) {
                config = $el.data(configName);
                if (config) {
                    break;
                }
                $el = $el.parent();
            }
        }
        return config || {};
    }


    /* SdiGrid PUBLIC CLASS DEFINITION
     * ================================= */

    var SdiGrid = function (element, options) {
        element = $(element);
        // More default options can be added as DOM data attribute
        // allowing a global config, with non-marshallable objects possible in it
        var cookedOptions = $.extend(true, {}, 
            $.fn.sdigrid.defaults,
            findDefaultOptions(element, options),
            options
        );
        this.init('sdigrid', element, cookedOptions);
    };


    SdiGrid.prototype = $.extend({}, $.fn.slickgrid.Constructor.prototype, {

        constructor: SdiGrid,

        postInit: function () {
            // Resolve non-JSON marshallable functions
            var o = this.wrapperOptions;
            o.originalColumns = o.columns;
            o.columns = this.processColumns(o.columns);
            // finish by calling handleCreate
            $.fn.slickgrid.Constructor.prototype.postInit.call(this);
        },

        processColumns: function (columns) {
            var results = [];
            var o = this.wrapperOptions;
            $.each(columns, function(index, columnDef) {
                var defaults = {};
                // id defaults to columnDef.field
                defaults.id = columnDef.field;
                // resolve formatter from map
                defaults.formatter = o.formatters[columnDef.formatterName];
                // resolve validator from map
                defaults.validator = o.validators[columnDef.validatorName];
                // resolve editor from map
                defaults.editor = o.editors[columnDef.editorName];
                // store it
                var newColumnDef = $.extend({}, defaults, columnDef);
                results.push(newColumnDef);
            });
            return results;
        }

    });

    /* SlickGrid PLUGIN DEFINITION */

    $.fn.sdigrid = function (option) {
        return this.each(function () {
            var $this = $(this),
                data = $this.data('sdigrid'),
                options = typeof option == 'object' && option;
            if (! data) {
                $this.data('sdigrid', (data = new SdiGrid(this, options)));
            }
            if (typeof option == 'string') {
                data[option]();
            }
        });
    };

    $.fn.sdigrid.Constructor = SdiGrid;

    $.fn.sdigrid.defaults = $.extend({}, $.fn.slickgrid.defaults, {
        //slickgridOptions: {},
        //columns: [],
        //columns: [],           // Column meta data in SlickGrid's format.
        //sortCol: null,         // the name of the initial sorting column
        //sortDir: true,         // sorting direction true = ascending, or false = descending
        //handleCreate: function() {}; -- This is called after the grid is created,
        //                                and can be used to customize the grid.
        //handleCreate: null     // This handler is called after the grid is created,
                                 // and it can be used to customize the grid.
                    // Variables you can access from this handler:
                    //
                    // this:                  will equal to the SlickGrid object instance
                    // this.element:          the element to bind the grid to
                    // this.wrapperOptions:   options passed to this object at creation

        configName: null,     // allows more default options, registered as DOM data with this key.
        formatters: {},
        validators: {},
        editors: {}
    });

})(window.jQuery);