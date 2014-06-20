/*jslint unparam: true, regexp: true */
/*global window, jQuery */

(function($) {
    'use strict';

    function getProgressFromData(data) {
        return parseInt(data.loaded / data.total * 100, 10);
    }

    function updateProgress(context, progress) {
        context.each(function() {
            $(this)
                .css('width', progress + '%')
                .text(progress + '%');
        });
    }

    function removeRow(el) {
        el.addClass('deleted');
        setTimeout(function() {
            el.remove();
        }, 1100);
    }

    function removeRows(context) {
        context.each(function() {
            removeRow($(this));
        });
    }

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
            removeRows($(this).closest('.alert'));
            // remove its files
            removeRows(context);
        });
        // Always reposition the global toolbar
        positionToolbar();
    }

    var url = './@@upload-submit',
        globalProgress = $('#progress .progress-bar'),
        UploadButton = $('<button class="upload-button" />')
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
                create: function() {
                    // create and return a new button
                    var self = UploadButton.clone(true);
                    var data = self.data();
                    data.self = self;
                    // set initial state
                    data.initialState();
                    // and return it
                    return self;
                },
                initialState: function() {
                    this.self
                        .text('Upload')
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
                        .text('Abort')
                        .removeClass('btn-success')
                        .addClass('btn-danger');
                    // add a promise for us
                    // to signal when finished
                    this.finished = $.Deferred();
                },
                finishedState: function() {
                    this.self.remove();
                    this.finished.resolve();
                },
                onSubmit: function(handler) {
                    this.handlers.submit.push(handler);
                },
                submit: function() {
                    // submit all sets of files
                    var all = [];
                    this.handlers.abort = [];
                    $.each(this.handlers.submit, function (index, handler) {
                        all.push(handler());
                    });
                    // make an 'all' promise from the individual promises
                    return $.when.apply(null, all);
                },
                abort: function() {
                    $.each(this.handlers.abort, function (index, handler) {
                        handler();
                    });
                    this.handlers.abort = [];
                }
            });
    $('#fileupload').fileupload({
        url: url,
        dataType: 'json',
        autoUpload: false,
        // XXX These settings do not make sense generically,
        // but they can be important in specific use cases.
        // For this reason, they should be settable on the folder.
        // TODO implement this once.
        //
        //acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i,
        //maxFileSize: 5000000, // 5 MB
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
        // XXX disable ...
        // enable multi file uploads, while limiting it with
        // a size (exceeding this a new request will be made)
        singleFileUploads: true,
        //limitMultiFileUploadSize: 5 * 1000 * 1000    // 5MB
    }).on('fileuploadadd', function (e, data) {
        data.context = $('<div class="container" />').appendTo('#files');
        // add a global upload button, if it does not exist yet
        var button = $('#fileupload-toolbar').find('.upload-button');
        if (button.length === 0) {
            button = UploadButton.data().create()
                .appendTo('#fileupload-buttons');
        }
        // Construct the upload info bar for all the files
        var template = $('#file-in-progress-template > div');
        $.each(data.files, function (index, file) {
            var newItem = template.clone().appendTo(data.context);
            newItem.find('.file-name').eq(0).text(file.name);
            newItem.find('.remove-button').click(function() {
                console.log('clicked!');
                var rowContainer = $(this).closest('.file-in-progress').parent();
                // Recalculate index of element as it will
                // differ from its index at creation
                var currentIndex = rowContainer.index('#files > *');
                // Remove this element from the file index
                data.files.splice(currentIndex);
                // Remove the row visually
                removeRow(rowContainer);
            });
        });
        // register the submit function on the button
        button.data().onSubmit($.proxy(data.submit, data));
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
        updateProgress(data.context.find('.progress .progress-bar'),
            getProgressFromData(data));
    }).on('fileuploadprogressall', function (e, data) {
        updateProgress(globalProgress, getProgressFromData(data));
    }).on('fileuploaddone', function (e, data) {
        // status for the user
        if (data.context) {
            data.context.each(function() {
            });
        }
        flash('success', data.result.files.length, data.context);
    }).on('fileuploadfail', function (e, data) {
        // status for the user
        flash('danger', data.files.length, data.context);
        //$.each(data.result.files, function (index, file) {
        //    console.log('ERROR file:', index, file);
        //});
    }).prop('disabled', !$.support.fileInput)
        .parent().addClass($.support.fileInput ? undefined : 'disabled');

    // Toolbar positioning
    function positionToolbar(evt) {
        // get the offset of the global progress wrapper
        var navbar = $('.navbar:first');
        var fixable = $('#fileupload-fixable-wrapper');
        var nextTop = fixable.next().offset().top;
        // we add some more margin that stays on top
        var margin = 8;
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
    }
    // Bind the toolbar's position fix.
    $(window).bind('scroll resize', positionToolbar);

})(jQuery);
