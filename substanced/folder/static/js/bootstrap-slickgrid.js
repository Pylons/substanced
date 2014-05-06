

!function ($) {

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


 /* SlickGrid PUBLIC CLASS DEFINITION
  * ================================= */

  var SlickGrid = function ( element, options ) {
    element = $(element);
    // More default options can be added as DOM data attribute
    // allowing a global config, with non-marshallable objects possible in it
    var moreDefaultOptions = findDefaultOptions(element, options);
    var cookedOptions = $.extend(true, {}, 
        $.fn.slickgrid.defaults, moreDefaultOptions, options);
    this.init('slickgrid', element, cookedOptions);
  }


  SlickGrid.prototype = {

    constructor: SlickGrid

  , init: function (type, element, options) {
        var self = this;
        this.element = $(element);
        this.wrapperOptions = options;

        // Resolve non-JSON marshallable functions
        this.columns = this.processColumns();

        // Call the provided hook to post-process.
        var handleCreate = this.wrapperOptions.handleCreate;
        if (handleCreate !== undefined) {
            handleCreate.apply(this);
        } else {
            this.handleCreate();
        }
    }

  , processColumns: function () {
        var self = this;
        var results = [];
        var options = this.wrapperOptions;
        $.each(options.columns, function(index, columnDef) {
            var defaults = {};
            // id defaults to columnDef.field
            defaults.id = columnDef.field;
            // resolve formatter from map
            defaults.formatter = options.formatters[columnDef.formatterName];
            // resolve validator from map
            defaults.validator = options.validators[columnDef.validatorName];
            // resolve editor from map
            defaults.editor = options.editors[columnDef.editorName];
            // store it
            var newColumnDef = $.extend({}, defaults, columnDef);
            results.push(newColumnDef);
        });
        return results;
    }

 ,  handleCreate: function () {
        // Create a simple grid configuration.
        //
        // This handler will run after the options
        // have been preprocessed. It can be overridden by passing
        // the handleCreate option at creation time.
        //
        // Variables you can access from this handler:
        //
        // this:                  will equal to the SlickGrid object instance
        // this.element:          the element to bind the grid to
        // this.columns:          column definitions (pre-processed)
        // this.wrapperOptions:   options passed to this object at creation
        //
        var dataView = new Slick.Data.DataView({inlineFilters: true});
        var grid = new Slick.Grid(this.element, dataView, this.columns, this.wrapperOptions.slickgridOptions);
        var columns = this.columns;

        var sortcol = columns[0].field;
        var sortdir = 1;
        function comparer(a, b) {
            var x = a[sortcol], y = b[sortcol];
            return (x == y ? 0 : (x > y ? 1 : -1));
        }

        grid.onSort.subscribe(function (e, args) {
            sortdir = args.sortAsc ? 1 : -1;
            sortcol = args.sortCol.field;

            dataView.sort(comparer, args.sortAsc);
        });

        // initialize the model after all the events have been hooked up
        dataView.beginUpdate();
        dataView.setItems(this.wrapperOptions.items);
        dataView.endUpdate();

        grid.render();

    }

  };

 /* SlickGrid PLUGIN DEFINITION */

  $.fn.slickgrid = function (option) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('slickgrid')
        , options = typeof option == 'object' && option
      if (!data) $this.data('slickgrid', (data = new SlickGrid(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  $.fn.slickgrid.Constructor = SlickGrid;

  $.fn.slickgrid.defaults = {
      slickgridOptions: {},
      columns: [],
      //sortCol: null,       // the name of the initial sorting column
      sortDir: true,         // sorting direction true = ascending, or false = descending
                             // (it will not sort really, just show it in the header)
      //configName: null     // allows more default options, registered as DOM data with this key. (...)
      formatters: {},
      validators: {},
      editors: {}
      // handleCreate: function() {}; -- This is called after the grid is created,
      //                                 and can be used to customize the grid.
      //                                 The function can access this.grid, this.dataView, ...
      // dataView: null  -- if this is not specified, we will create one
      //                    and store it in this.dataView.
  }

}(window.jQuery);

