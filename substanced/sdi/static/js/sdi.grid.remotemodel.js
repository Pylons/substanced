
/*jslint undef: true, newcap: true, nomen: false, white: true, regexp: true */
/*jslint plusplus: false, bitwise: true, maxerr: 50, maxlen: 110, indent: 4 */
/*jslint sub: true */
/*globals window navigator document */
/*globals setTimeout clearTimeout setInterval */ 
/*globals jQuery Slick alert confirm */


(function ($) {

    var log = function () {
        var c = window.console;
        if (c && c.log) {
            c.log(Array.prototype.slice.call(arguments));
        }
    };


    /* 
     * SlickGrid's remote data manager, customized for SDI.
     * OO coding model follows SlickGrid's plugin convention.
     *
     * Usage::
     *
     *     var sdiRemoteModelPlugin = new Slick.Data.SdiRemoteModel({
     *         url: '....',
     *         sortCol: 'title',
     *         sortDir: true, // or, false for descending.
     *         extraQuery: {},
     *         minimumLoad: 100
     *     });
     *     grid.registerPlugin(sdiRemoteModelPlugin);
     *
     *     sdiRemoteModelPlugin.onDataLoaded.subscribe(function (evt, args) {
     *         ...
     *     });
     *
     *
     * When the client queries the server for data, the 
     * server will receive the following query parameters:
     *
     *     from, to, sortCol, sortDir, + everything from extraQuery.
     *
     */

    var _createdQ = false;
    var _qName = 'sdigridloaderQueue';

    function _createQ() {
        if (! _createdQ) {
            $.manageAjax.create(_qName, {
                queue: true,
                maxRequests: 1
            });
            _createdQ = true;
        }
    }


    function SdiRemoteModel(_options) {

        // default options
        var options = {
            //url: null,         // the url of the server side search
            manageQueue: true,   // if to use the ajax queue manager
            //sortCol: null,
            sortDir: true,       // true = ascending, false = descending.
            reallyAbort: false   // Really abort all the outgoing requests. Set this to false,
                                 // if a real abort is undesirable. Note that independently of this
                                 // setting, the data clearings (resort, or refilter) always do an abort.
                                 // XXX we keep this false, as it seems the abort
                                 // actually causes more requests
            //extraQuery: {}     // Additional parameters that will be passed to the server.
        };

        var grid;
        var data;
        var _active_request;
        var scrollPosition;  // scrolling movement (prefetch) forward or backward

        // events
        var onDataLoading = new Slick.Event();
        var onDataLoaded = new Slick.Event();

        var ensureData; // STFU jslint

        function handleGridViewportChanged(evt, args) {
            var vp = grid.getViewport();
            var top = vp.top;
            var bottom = vp.bottom;
            var direction = top >= scrollPosition ? +1 : -1;
            ensureData(top, bottom, direction);
            scrollPosition = top;
        }

        function init(_grid) {
            grid = _grid;
            $.extend(options, _options);

            // ajax queue management
            if (options.manageQueue) {
                // Is the code present?
                if (! $.manageAjax) {
                    throw new Error('The jquery.ajaxmanager.js must be loaded, if the grid is ' +
                        'created with the default option manageQueue=true.');
                }
                // Sadly, there is no way to check if a given named queue
                // exists.... so we need to do this globally
                _createQ();
            }
            _active_request = null;

            // Bind our data to the grid.
            data = {length: 0};
            grid.setData(data);

            // scrolling
            scrollPosition = -1;  // force movement forward
            grid.onViewportChanged.subscribe(handleGridViewportChanged);
        }

        function _abortRequest(force) {
            // (Note that in case the queue manager is used,
            // 'undefined' is a valid, non-null result for the
            // _active_request id. So, we _always_ check against 'null'!)
            // The 'force' parameter is set true when a clear data is complete
            // (on change of sorting or filtering), otherwise the 'reallyAbort'
            // parameter specifies if a physical abort is being performed.
            if (_active_request !== null) {
                // abort the previous request
                if (options.manageQueue) {
                    $.manageAjax.clear(_qName, force || options.reallyAbort);
                } else {
                    if (force || options.reallyAbort) {
                        _active_request.abort();
                    }
                }
            }
            _active_request = null;
        }

        function destroy() {
            // Just abort the request, make sure it always happens
            _abortRequest(true);
            // (be paranoid about IE memory leaks)
            data = null;
        }

        function clearData() {
            // Delete the data
            $.each(data, function (key, value) {
                delete data[key];
            });
            // We force to abort all requests, even if reallyAbort=false
            _abortRequest(true);
            // let the viewport load records currently visible
            grid.invalidateAllRows();
            grid.onViewportChanged.notify();
        }

        function loadData(_data) {
            var from = _data.from,
                to = _data.to,
                i;
            for (i = from; i < to; i++) {
                data[i] = _data.records[i - from];
            }
            data.length = _data.total;
            // Update the grid.
            grid.updateRowCount();
            grid.render();
        }

        function _ajaxSuccess(_data) {
            loadData(_data);
        }

        function _ajaxError(xhr, textStatus, errorThrown) {
            if (textStatus != 'abort') {
                log('error: ' + textStatus);
            }
        }

        function _invalidateRows(data) {
            // invalidate rows for the received data.
            if (data && data.from !== undefined) {
                var i;
                for (i = data.from; i < data.to; i++) {
                    grid.invalidateRow(i);
                }
                grid.updateRowCount();
                grid.render();
            }
        }

        ensureData = function (from, to, direction) {
            //log('Records in viewport:', from, to, direction);
            // abort the previous request
            _abortRequest();

            if (from < 0) {
                throw new Error('"from" must not be negative');
            }
            if (from >= to) {
                throw new Error('"to" must be greater than "from"');
            }

            var start;
            var end;
            if (direction == +1) {
                start = from;
                end = to - 1;
            } else {
                start = to - 1;
                end = from;
            }

            // do we have all records in the viewport?
            var i = start;
            var firstMissing = null;
            var lastMissing = null;
            while (true) {
                if (! data[i]) {
                    if (firstMissing === null) {
                        firstMissing = i;
                    }
                    lastMissing = i;
                }
                if (i == end) {
                    break;
                }
                i += direction;
            }

            if (firstMissing === null) {
                // All records present.
                // We can return, nothing to fetch.
                //log('Has already', start, end);
                //
                // must trigger loaded, even if no actual data
                onDataLoaded.notify({});
                return;
            }

            start = firstMissing;
            end = lastMissing;

            //log('Missing:', firstMissing, lastMissing);

            // Load at least minimumLoad records
            if (options.minimumLoad && (to - from) < options.minimumLoad) {
                end = start + direction * options.minimumLoad - 1;
            }

            // Sort start and end now, and we can start loading.
            if (start > end) {
                from = end;
                to = start;
            } else {
                from = start;
                to = end;
            }
            if (from < 0) {
                from = 0;
            }
            // 'to' is the last item now = make it an index.
            to += 1;

            //log('Will load:', from, to, direction);

            onDataLoading.notify({from: from, to: to});

            var ajaxOptions = {
                type: "GET",
                url: options.url,
                data: $.extend({
                    from: from,
                    to: to,
                    sortCol: options.sortCol,
                    sortDir: options.sortDir
                }, (options.extraQuery || {})),
                success: function (data) {
                    // XXX It seems, that IE bumps us
                    // here on abort(), with data=null.
                    if (data !== null) {
                        _ajaxSuccess(data);
                    }
                    _active_request = null;
                    _invalidateRows(data);
                    onDataLoaded.notify(data);
                },
                error: function (xhr, textStatus, errorThrow) {
                    _active_request = null;
                    _ajaxError(xhr, textStatus, errorThrow);
                },
                dataType: 'json'
            };

            if (options.manageQueue) {
                _active_request = $.manageAjax.add(_qName, ajaxOptions);
            } else {
                _active_request = $.ajax(ajaxOptions);
            }
        };

        function setSorting(sortCol, sortDir) {
            if (options.sortCol != sortCol || options.sortDir != sortDir) {
                options.sortCol = sortCol;
                options.sortDir = sortDir;
                // notify the grid
                clearData();
            }
        }

        function setFilterArgs(o) {
            var changed;
            $.each(o, function (key, value) {
                if (options.extraQuery[key] !== o[key]) {
                    options.extraQuery[key] = o[key];
                    changed = true;
                }
            });
            // notify the grid if any of the filters changed
            if (changed) {
                clearData();
            }
        }

        // --
        // synchronize selections, needed if sorting changed.
        // -- 
        
        function mapRowsToIds(rowArray) {
            var ids = {};
            $.each(rowArray, function (index, rowIndex) {
                var row = data[rowIndex];
                ids[row.id] = true;
            });
            return ids;
        }
   
        function mapIdsToRows(ids, from, to) {
            var rows = [];
            var i;
            //log('mapIdsToRows', from, to, data[from]);
            for (i = from; i < to; i++) {
                if (data[i] !== undefined) {
                    if (ids[data[i].id]) {
                        rows.push(i);
                    }
                }
            }
            return rows;
        }

        function syncGridSelection(preserveHidden) {
            var self = this;
            var selectedRowIds = mapRowsToIds(grid.getSelectedRows());
            var inHandler;

            grid.onSelectedRowsChanged.subscribe(function (e, args) {
                if (inHandler) {
                    return;
                }
                // save selections
                selectedRowIds = mapRowsToIds(grid.getSelectedRows());
                //log('saved', selectedRowIds);
            });

            onDataLoaded.subscribe(function (evt, args) {
                if (args.from !== undefined) {
                    // restore selections
                    inHandler = true;
                    var selectedRows = mapIdsToRows(selectedRowIds, args.from, args.to);
                    log(2, selectedRows);
                    if (! preserveHidden) {
                        selectedRowIds = mapRowsToIds(selectedRows);
                    }
                    grid.setSelectedRows(selectedRows);
                    inHandler = false;
                }
            });
        }


        // Things we offer as public.
        return {
            // properties
            data: data,
            grid: grid,
            options: options,

            // methods
            init: init,
            destroy: destroy,

            clearData: clearData,
            loadData: loadData,
            ensureData: ensureData,
            setSorting: setSorting,
            setFilterArgs: setFilterArgs,
            syncGridSelection: syncGridSelection,

            // events
            onDataLoading: onDataLoading,
            onDataLoaded: onDataLoaded
        };
    }

    // Slick.Data.SdiRemoteModel
    $.extend(true, window, {Slick: {Data: {SdiRemoteModel: SdiRemoteModel}}});

})(jQuery);
