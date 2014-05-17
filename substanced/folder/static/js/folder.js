var folder = function() {

    load_contents = function(options) {

        function redraw(e) {
            var gridWrapper = $('#sdi-contents-table-sg').data('slickgrid');
            plugin = gridWrapper.sdiRemoteModelPlugin;
            if (!plugin.hasActiveRequest()) {
                // only do one request at a time
                plugin.resetData();
            }
            // remove the error messages XXX XXX
            $('.contents-error').remove();
        }


        // update UI in real-time based if the browser supports SSE
        var reconnectTimer;
        var source;
        function connectEventSource() {
            if (source) {
                source.close();
            }
            source = new EventSource(options.eventSource);
            source.addEventListener("ContentAdded" , redraw);
            source.addEventListener("ContentRemoved" , redraw);
            source.addEventListener("ContentMoved" , redraw);
            source.addEventListener("ContentDuplicated" , redraw);
            source.addEventListener('error', function(evt) {
                var current = evt.currentTarget;
                var state;
                if (current.readyState == EventSource.OPEN) {
                    state = 'OPEN';
                    if (reconnectTimer) {
                        clearTimeout(reconnectTimer);
                    }
                }
                if (current.readyState == EventSource.CLOSED) {
                    state = 'CLOSED';
                    if (reconnectTimer) {
                        clearTimeout(reconnectTimer);
                    }
                    reconnectTimer = setTimeout(function() {
                        console.log('RECONNECT');
                        connectEventSource();
                    }, 10000);
                }
                if (current.readyState == EventSource.CONNECTING) {
                    state = 'CONNECTING';
                    if (reconnectTimer) {
                        try {
                            clearTimeout(reconnectTimer);
                        } catch(e) {
                        }
                    }
                    if ($('.contents-error').length > 0) {
                        // Remove previous error status messages, if any.
                        $('.contents-error').remove();
                        // redraw the grid
                        redraw();
                    }
                }
                console.log('EventSource state:', state);
            });
        }
        if (!!window.EventSource) {
            connectEventSource();
        }


        // --
        // grid buttons
        // --

        var $form =  $('#contents_form');

        // prevent form submission from happening when enter is pressed
        $form.keypress( function(evt) {
            return !(evt.which==13 && evt.target.type!='textarea');
        });
        // this prevents submit also by spacebar (keyCode==32)
        $('#contents_form input[type="submit"]').attr('tabIndex',-1);

        var $hiddenInput =  $form.find('input[name="item-modify"]');

        // If a button is clicked, get the selections out of the grid,
        // and add it to a form as a hidden field.
        $form.find('button').click(function (evt) {
            var gridWrapper = $('#sdi-contents-table-sg').data('slickgrid');
            var grid = gridWrapper.grid;
            var selRows = grid.getSelectedRows();
            if (selRows.length > 100) {
                // XXX XXX XXX This is a problem. We need to limit
                // the selection size, because of cookieval is limited
                // in 4096 bytes. An additional problem is we don't know
                // how to limit the selection size to assure that the submit
                // won't break, because the cookie size depends on the lengths
                // of the names, too, and not only on the size of the selection.
                // TODO this must be solved somehow!
                alert('We currently limit the selection size in maximum 100 items.\n' +
                      'Please select less than 100 items!');
                return false;
            }
            var data = grid.getData();
            var selectedIds = $.map(selRows, function (value, index) {
                var row = data[value];
                return (row || {}).id;
            });
            // I think it is better to submit the list as a
            // concatenated value, instead of adding several inputs to the dom.
            $hiddenInput.attr('value', selectedIds.join('/'));
        });


        // --
        // grid creation
        // --

        $(document).ajaxStart(sdi.loading_indicator_on);
        $(document).ajaxStop(sdi.loading_indicator_off);

        var $grid = $('#sdi-contents-table-sg');
        var $filter = $('.sdi-contents-filter input');
        // grid
        $grid.slickgrid(options.slickgridWrapperOptions);
        var gridWrapper = $grid.data('slickgrid');

        // delay for filter helps to reduce
        // the number of requests while typing
        // continually.
        var filterTimer;
        var filterDelay = 500;       // millis
        function delayedAction(inner) {
            if (filterTimer) {
                clearTimeout(filterTimer);
            }
            filterTimer = setTimeout(inner, filterDelay);
        }

        // filter
        $filter.on('keyup', function (evt) {
            delayedAction(function () {
                gridWrapper.setSearchString($filter.val());
            });
        });

        // Clear filter, issue 47
        $('#sdi-contents-filter-clear')
            .on('click', function () {
                $filter
                    .val('')
                    .trigger('keyup');
                return false;
            });

        // Update the buttons if the selection has changed.
        var grid = gridWrapper.grid;
        grid.onSelectedRowsChanged.subscribe(function (evt) {
            var selRows = grid.getSelectedRows();
            var data = grid.getData();
            var disabled = [];
            if (selRows.length) {
                var disable_multiple = false;
                var i;
                for (i = 0, l = selRows.length; i < l; i++) {
                    var item = data[selRows[i]];
                    // XXX bug: global selection will select all items that
                    // are not present.
                    disabled[i] = item.disable;
                    if (i == 1) {
                        disable_multiple = true;
                    }
                }
                $('.btn-sdi-sel').attr('disabled', false);
                $('.btn-sdi-one').attr('disabled', disable_multiple);
                for (i = 0, l = selRows.length; i < l; i++) {
                    if (disabled[i]) {
                        for (var j = 0, k = disabled[i].length; j < k; j++) {
                            $('#' + disabled[i][j]).attr('disabled', true);
                        }
                    }
                }
            } else {
                $('.btn-sdi-sel').attr('disabled', true);
                $('.btn-sdi-one').attr('disabled', true);
            }
        });

        // Inject flash messages that arrive from the server via ajax.
        gridWrapper.sdiRemoteModelPlugin.onDataLoaded.subscribe(function (evt, args) {
            if (args.flash && args.flash_queue) {
                // Clear existing messages, and add this one.
                $('#messages')
                    .empty()
                    .append(
                        $('<div class="alert alert-' + args.flash_queue + '"></div>')
                            .append(args.flash).append('<button type="button" class="close" data-dismiss="alert">&times;</button>')
                    );
            }
            // Remove previous error status messages, if any.
            $('.contents-error').remove();
        });

        // handle errors
        gridWrapper.sdiRemoteModelPlugin.onAjaxError.subscribe(function (evt, args) {
            // If we have an Unauthenticated, we get a parse error. We try to figure
            // out from the response html, if this has happened because our session
            // has expired.
            if (args.textStatus == 'parsererror' &&
                args.xhr.responseText.indexOf('Not logged in') != -1) {
                if ($('.contents-ajax-unauthorized').length === 0) {
                    // Let's display it a status message in case the user clicks cancel.
                    $('#messages')
                        .append(
                            $('<div class="alert alert-danger contents-error contents-ajax-unauthorized"></div>')
                                .append('It looks like your authentication session has expired.<br>' +
                                        'You can ' +
                                        '<a class="contents-ajax-error-reload" href="#"> reload the page</a>.'
                                       )
                        );
                    // Suggest the user to reload the page which will enable her to login.
                    if (confirm('It looks like your authentication session has expired.\n' +
                                'Do you wish to leave the page, and log in again?')) {
                        document.location.reload();
                    }
                }
            } else if ((args.errorThrown !== 'Internal Server Error') && (args.textStatus === 'error')) {
                // We have a connection problem. Display a message if it's not already on.
                if ($('.contents-ajax-error').length === 0) {
                    $('#messages')
                        .append(
                            $('<div class="alert alert-danger contents-error contents-ajax-error"><button type="button" class="close" data-dismiss="alert">&times;</button></div>')
                                .append('Error reaching the server. This is probably a temporary error.<br>' +
                                        'If your network connection resumes, ' +
                                        'the error state should resolve by itself. You can also ' +
                                        '<a class="contents-ajax-error-reload" href="#"> reload the page</a>.'
                                       )
                        );
                }
            }
            $('.contents-ajax-error-reload').click(function() {
                document.location.reload();
                return false;
            });
        });

    };            // end load_contents()

    return {load_contents:load_contents};

}();

