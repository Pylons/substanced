
/* jshint undef: true */
/* global document, window, jQuery, setTimeout, clearTimeout, moment */

(function($) {
    "use strict";

    var dropZoneClassName = 'dropzone';
    var disableDropZoneClassName = 'add-files-disabled';
    var fileUploadClassName = 'file-upload';

    // Trigger a resize.
    var triggerResize = function() {
        window.dispatchEvent(new window.Event('resize'));
    };
    // Trigger an initial resize.
    triggerResize();

    // set a class if we have html5 xhr upload.
    if (window.FormData) {
        $('body').addClass(fileUploadClassName);
    }

    function isUploadInProgress() {
        return $('body').hasClass(disableDropZoneClassName);
    }

    function sizeToText(n, unitType) {
        // Return in the correct unit of TB, GB, MB, KB, B
        // Powers of 1024 are used: 1 MB = 1024 KB and so on.
        // XXX check the correct convention and units.
        var power = Math.pow(2, 10);
        var units = {
            'B': ['B', 'KiB', 'MiB', 'GiB', 'TiB'],
            'B/s': ['B/s', 'KiB/s', 'MiB/s', 'TiB/s']
        }[unitType];
        if (n === 0) {
            // special case: would yield Infinity
            // at the logarithm below.
            return '0 ' + units[0];
        }
        // Divide it until it reaches its correct unit
        while (units.length > 1 && n >= power) {
            n = n / power;
            units.shift();
        }
        // Show 3 digits including the decimals.
        // Examples: 321 4.32K 54.3K 654K 7.65M 87.6M ...
        // parseFloat is used to trim trailing zeroes.
        return '' + parseFloat(n.toFixed(Math.max(0,
            2 - Math.floor(Math.log(n) / Math.LN10)
        ))) + ' ' + units[0];
    }

    function updateGlobalProgress(data) {
        if (data === undefined) {
            // If data is not specified, fetch the value
            data = $('#fileupload').fileupload('progress');
        }
        updateProgress(globalProgress, getProgressFromData(data));
        // Update the transfer rate too
        $('#fileupload-global-bitrate').text(sizeToText(data.bitrate / 8, 'B/s'));

    }

    function getProgressFromData(data) {
        return parseInt(data.loaded / data.total * 100, 10);
    }

    function updateProgress(context, progress) {
        context.each(function() {
            var bar = $(this);
            bar.css('width', progress + '%');
            bar.text(progress > 0 ? progress + '%' : '');
        });
    }

    function removeRow(el) {
        // remove row from sums
        var item = el.find('.file-in-progress');
        // but only for file items, skip when call for a status box
        // which has no .file-in-progress contained.
        if (item.length > 0) {
            var undoSums = item.data().undoSums;
            if (undoSums) {
                undoSums();
            }
        }
        // animate removal
        el.addClass('deleted');
        setTimeout(function() {
            el.remove();
        //
        // this timeout must match the 'disappear' animation's timing,
        //  e.g. for 450:
        //
        //    -webkit-animation: disappear 0.45s;
        //    -webkit-animation-fill-mode: forwards;
        //    animation: disappear 0.45s;
        //    animation-fill-mode: forwards;
        //
        }, 450);
    }

    function removeRows(context) {
        context.each(function() {
            removeRow($(this));
        });
    }

    // Singleton to display sums in the fileupload toolbar
    var Sums = {
        count: 0,
        size: 0,
        add: function(file) {
            var self = this;
            this.count += 1;
            this.size += file.size;
            this.update();
            // make the file info immutable
            // to protect against possible modification
            file = {size: file.size};
            // return a handler to remove
            // the file from the sum
            return function() {
                self.remove(file);
            };
        },
        remove: function(file) {
            this.count -= 1;
            this.size -= file.size;

            this.update();
        },
        update: function() {
            $('#fileupload-global-count').text(
                '' + this.count +
                ' file' + (this.count >= 2 ? 's' : '')
            );
            $('#fileupload-global-size').text(sizeToText(this.size, 'B'));
            // Also update the global progress bar.
            // But since it would keep the last value
            // (perhaps this is a bug in the upstream software?),
            // we will just display a zero both on add and cancel.
            // Skip update, if we are in an upload progress, as then
            // it's taken care of until the end of the update.
            if (! isUploadInProgress()) {
                updateGlobalProgress({total: 1, loaded: 0, bitrate: 0});
            }
        }
    };

    function flash(alertType, diff, context) {
        // Flash into our own #fileupload-messages bar.
        // We do not use #messages because this way we can
        // include the messages into the fixable region that
        // always stays on top.
        // 
        // Alert type is either 'success' or 'error'.
        // Diff is a positive value.
        //
        // is there already a flash for this alert type?
        var flashBox = $('#fileupload-messages').find('.alert-fileupload-' + alertType).last();
        if (flashBox.length === 0) {
            // If not, create it.
            // data-
            flashBox = $('<div class="alert alert-' + alertType +
                      ' alert-fileupload-' + alertType + '"></div>')
                .append('<span class="status"></span>')
                .append('<button type="button" class="close">&times;</button>')
                .data({
                    nr: 0,
                    increment: function(diff) {
                        this.nr += diff;
                        flashBox.find('.status').text(
                            ((this.nr < 2) ? {
                                // singular
                                success: '' + this.nr + ' file uploaded',
                                danger: 'Upload failed for ' + this.nr + ' file'
                            } : {
                                // plural
                                success: '' + this.nr + ' files uploaded',
                                danger: 'Upload failed for ' + this.nr + ' files'
                            })[alertType]
                        );
                    }
                })
                .appendTo('#fileupload-messages');
        }
        // Increment the counter with the diff specified.
        flashBox.data().increment(diff);
        // closing the status box will remove its files 
        flashBox.find('.close').click(function() {
            // close the box
            removeRow($(this).closest('.alert'));
            // remove its files
            removeRows(context);
        });
        // Always reposition the global toolbar
        triggerResize();
    }

    var url = './@@upload-submit',
        globalProgress = $('#progress .progress-bar');

    //
    // The prototype of the upload button. Usage:
    //
    //      var uploadButton = UploadButton.data().create();
    //
    var UploadButton = $('<button class="upload-button" />')
        .addClass('btn')
        .prop('disabled', true)
        .on('click', function () {
            var data = $(this).data();
            data.uploadState();
            data.self.on('click', function () {
                data.finishedState();
                data.abort();
            });
            data.submit().always(function () {
                data.finishedState();
            });
        })
        .data({
            //
            // create method
            //
            // It should be called on UploadButton.data().
            //
            create: function() {
                // Create and return a new button.
                var uploadButton = UploadButton.clone(true);
                var data = uploadButton.data();
                data.self = uploadButton;
                // Set initial state,
                data.initialState();
                // and return it.
                return uploadButton;
            },
            //
            // Instance methods
            //
            // Taken a button returned by create(), they should
            // be called on button.data().
            //
            initialState: function() {
                this.self
                    .html('<i class="glyphicon glyphicon-upload"></i> ' +
                          'Upload')
                    .prop('disabled', !!(this.files || []).error)
                    .removeClass('btn-danger')
                    .addClass('btn-success');
                this.handlers = {};
                this.handlers.submit = [];
                this.handlers.abort = [];
            },
            uploadState: function() {
                this.self
                    .off('click')
                    .html('<i class="glyphicon glyphicon-remove"></i> ' +
                          'Abort')
                    .removeClass('btn-success')
                    .addClass('btn-danger');
                // add a promise for us
                // to signal when finished
                this.finished = $.Deferred();
            },
            finishedState: function() {
                // enable Add button
                $('#fileupload')
                    .prop('disabled', false)
                    .parent().removeClass('disabled');
                $('body').removeClass(disableDropZoneClassName);
                this.self.remove();
                this.finished.resolve();
            },
            onSubmit: function(handler) {
                var a = this.handlers.submit;
                a.push(handler);
                // return a function that can delete the handler
                return function() {
                    a.splice(a.indexOf(handler), 1);
                };
            },
            submit: function() {
                // disable Add button
                $('#fileupload')
                    .prop('disabled', true)
                    .parent().addClass('disabled');
                $('body').addClass(disableDropZoneClassName);
                // submit all sets of files
                var all = [];
                this.handlers.abort = [];
                $.each(this.handlers.submit, function(index, handler) {
                    all.push(handler());
                });
                // Make an 'all' promise from the individual promises.
                // $.when.apply(null, all) is jQuery's odd way of saying
                // "wait until all the promises in 'all' are resolved".
                return $.when.apply(null, all);
            },
            abort: function() {
                $.each(this.handlers.abort, function(index, handler) {
                    handler();
                });
                this.handlers.abort = [];
            }
        });

    //
    // The jquery-fileupload component binds on the Add File button.
    //
    $('#fileupload').fileupload({
        url: url,
        dataType: 'json',
        autoUpload: false,
        // XXX The current defaults match best the generic use case.
        // Uncommenting some of these setting would however make sense
        // in specific use cases. For this reason, it would be best if
        // they would become settable as properties on the folder.
        // TODO implement this once.
        //
        // acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i,
        // maxFileSize: 5000000, // 5 MB
        //
        // Enable image resizing, except for Android and Opera,
        // which actually support image resizing, but fail to
        // send Blob objects via XHR requests.
        // By default images are resized to FullHD (1920x1080).
        disableImageResize: /Android(?!.*Chrome)|Opera/
            .test(window.navigator.userAgent),
        previewMaxWidth: 65,
        previewMaxHeight: 65,
        previewCrop: true,
        // Do not enable multi file uploads, as keeping each file
        // in its own physical request is necessary for the proper support
        // of individual progress bars.
        // XXX Supporting both single and multi file payloads could be a TODO
        // for the future, as many small files could scale better
        // with multi file payload enabled.
        singleFileUploads: true,
    }).on('fileuploadadd', function (e, data) {
        data.context = $('<div class="container" />').appendTo('#files');
        // add a global upload button, if it does not exist yet
        var uploadButton = $('#fileupload-toolbar').find('.upload-button');
        if (uploadButton.length === 0) {
            uploadButton = UploadButton.data().create()
                .appendTo('#fileupload-buttons');
        }
        // Construct the upload info bar for all the files
        var uploadButtonData = uploadButton.data();
        var template = $('#file-in-progress-template > div');
        var allContainers = $('#files > *');
        $.each(data.files, function (index, file) {
            var newItem = template.clone().appendTo(data.context);
            var canvasWrapper = newItem.find('.canvas-wrapper');
            var fileIcon = canvasWrapper.find('.file-icon');
            var fileInfo = newItem.find('.file-info');
            var fileName = newItem.find('.file-name');
            var fileSize = newItem.find('.file-size');
            var fileModified = newItem.find('.file-modified');
            if (file.type) {
                fileIcon.addClass('mimetype-icon-' + file.type.split('/', 2)[1]);
            }
            fileName.text(file.name);
            fileSize.text(sizeToText(file.size, 'B'));
            fileModified.text(moment(file.lastModifiedDate).format('LL'));
            newItem.find('.remove-button').click(function() {
                // Remove the file from the submit queue.
                cancelSubmit();
                // Remove the row visually
                removeRow($(this).closest('.file-in-progress').parent());
            });
            // report the addition of this file to the toolbar
            newItem.data().undoSums = Sums.add(file);
        });
        // register the submit function on the button
        var cancelSubmit = uploadButton.data().onSubmit($.proxy(data.submit, data));
    }).on('fileuploadprocessalways', function (e, data) {
        var index = data.index,
            file = data.files[index],
            node = $(data.context.children()[index]);
        if (file.preview) {
            node.find('.canvas-wrapper')
                .append(file.preview);
        }
        if (file.error) {
            node
                .append('<br>')
                .append($('<span class="text-danger"/>').text(file.error));
        }
    }).on('fileuploadprogress', function (e, data) {
        // make sure cancel button is removed, will happen at upload start
        data.context.find('.remove-button').remove();
        // update progress for single file
        updateProgress(data.context.find('.progress .progress-bar'),
            getProgressFromData(data));
    }).on('fileuploadprogressall', function (e, data) {
        // update global progress in toolbar
        updateGlobalProgress(data);
    }).on('fileuploaddone', function (e, data) {
        // status for the user
        if (data.context) {
            if (data.result.files.length != 1) {
                // Due to single file upload, we should lways have 1 here.
                // Check this as otherwise it would break.
                throw new Error('Fatal error, we should be doing single file uploads.');
            }
            // The server told us the real id of the file. Construct a link from this.
            var realName = data.result.files[0].name;
            $(data.context[0]).find('.file-name').wrap(
                $('<a/>')
                    .addClass('file-name-link')
                    .attr('href', realName + '/@@manage_main')
                    .attr('target', '_blank')
            );
        }
        flash('success', data.result.files.length, data.context);
    }).on('fileuploadfail', function (e, data) {
        // Ignore failing event if it's caused by user removing a file.
        // In this case, length will be 0.
        //if (data.files.length > 0) {
            // status for the user
            flash('danger', data.files.length, data.context);
            //$.each(data.result.files, function (index, file) {
            //    console.log('ERROR file:', index, file);
            //});
        //}
    }).on('fileuploaddrop', function (e, data) {
        if (isUploadInProgress()) {
            // we cannot drop now, let's abort the drop.
            return false;
        }
    }).prop('disabled', !$.support.fileInput)
        .parent().addClass($.support.fileInput ? undefined : 'disabled');

    //
    // Toolbar sticky positioning
    //
    $(window).bind('scroll resize', function() {
        // get the offset of the global progress wrapper
        var navbar = $('.navbar:first');
        var fixable = $('#fileupload-fixable-wrapper');
        var nextTop = fixable.next().offset().top;
        // we add some more margin that stays on top
        var margin = 7;
        // we calculate the height to be shown on top
        // this is the sum of the toolbar and messages height
        var showOnTop = margin + fixable.outerHeight();
        // decide if we are above or over the switch limit
        var navbarBottom = navbar.offset().top + navbar.height();
        var switchBottom = navbarBottom + showOnTop;
        if (nextTop < switchBottom) {
            fixable.css({
                'position': 'relative',
                'top': '' + (switchBottom - nextTop) + 'px'
            });
        } else {
            fixable.css({
                'position': 'static'
            });
        }
    });

    //
    // Drop zone effect
    // 
    // (The entire document is the drop zone.)
    //
    $(document).bind('dragover', function(evt) {
        var body = $('body'),
            timeout = window.dropZoneTimeout;
        if (isUploadInProgress()) {
            // we cannot drop now, let's return with cancel.
            return false;
        }
        if (! timeout) {
            body.addClass(dropZoneClassName);
        } else {
            clearTimeout(timeout);
        }
        window.dropZoneTimeout = setTimeout(function() {
            window.dropZoneTimeout = null;
            body.removeClass(dropZoneClassName);
        }, 100);
    });

})(jQuery);
