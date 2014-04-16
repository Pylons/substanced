/*jslint unparam: true, regexp: true */
/*global window, jQuery */

+(function($) {
    'use strict';

    function flash(alertType, diff) {
        // Alert type is either 'success' or 'error'.
        // Diff is (sensibly) positive.
        //
        // is there already a flash for this alert type?
        var flashBox = $('#messages').find('.alert-fileupload-' + alertType).last();
        if (flashBox.length === 0) {
            // If not, create it.
            flashBox = $('<div class="alert alert-' + alertType +
                      ' alert-fileupload-' + alertType + '"></div>')
                .append({
                    success: '<span class="nr">0</span> file(s) uploaded',
                    error: 'Upload failed for <span class="nr">0</span> file(s)'
                }[alertType])
                .append('<button type="button" class="close" data-dismiss="alert">&times;</button>')
                .data({
                    nr: 0,
                    increment: function(diff) {
                        this.nr += diff;
                        flashBox.find('.nr').text(this.nr);
                    }
                })
                .appendTo('#messages');
        }
        // Increment the counter with the diff specified.
        flashBox.data().increment(diff);
    }

    var url = './@@upload-submit',
        uploadButton = $('<button class="upload-button" />')
            .addClass('btn btn-primary')
            .prop('disabled', true)
            .on('click', function () {
                var $this = $(this),
                    data = $this.data();
                $this
                    .off('click')
                    .text('Abort')
                    .on('click', function () {
                        $this.remove();
                        data.abort();
                    });
                data.submit().always(function () {
                    $this.remove();
                });
            });
    $('#fileupload').fileupload({
        url: url,
        dataType: 'json',
        autoUpload: false,
        //acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i,
        //maxFileSize: 5000000, // 5 MB
        // Enable image resizing, except for Android and Opera,
        // which actually support image resizing, but fail to
        // send Blob objects via XHR requests.
        // By default images are resized to FullHD (1920x1080).
        disableImageResize: /Android(?!.*Chrome)|Opera/
            .test(window.navigator.userAgent),
        previewMaxWidth: 100,
        previewMaxHeight: 100,
        previewCrop: true,
        // enable multi file uploads, while limiting it with
        // a size (exceeding this a new request will be made)
        singleFileUploads: false,
        limitMultiFileUploadSize: 5 * 1000 * 1000    // 5MB
    }).on('fileuploadadd', function (e, data) {
        data.context = $('<div/>').appendTo('#files');
        // add a global upload button
        // is there already one?
        var button = $('#fileupload-wrapper').find('.upload-button');
        if (button.length === 0) {
            // add a new one
            button = uploadButton
                .clone(true)
                .data({
                    // dataItems aggregates all individual upload instances
                    dataItems: [],
                    submit: function() {
                        var all = [];
                        $.each(this.dataItems, function (index, dataItem) {
                            if (!dataItem.done) {
                                all.push(dataItem.submit());
                            }
                        });
                        return $.when.apply(null, all);
                    }
                })
                .text('Upload')
                .prop('disabled', false)
                .appendTo('#fileupload-wrapper');
        }
        var globalData = button.data();
        // Add individual upload buttons
        $.each(data.files, function (index, file) {
            var node = $('<p/>')
                .append($('<span/>').text(file.name));
            if (index === 0) {
                node
                    .append('<br>');
                    // TODO individal buttons
                    //.append(uploadButton.clone(true).data(data));
            }
            node.appendTo(data.context);
            // Add the files to the global button
            globalData.dataItems = globalData.dataItems.concat(data);
        });
        // reset progress
        $('#progress .progress-bar').css('width', 0);
    }).on('fileuploadprocessalways', function (e, data) {
        var index = data.index,
            file = data.files[index],
            node = $(data.context.children()[index]);
        if (file.preview) {
            node
                .prepend('<br>')
                .prepend(file.preview);
        }
        if (file.error) {
            node
                .append('<br>')
                .append($('<span class="text-danger"/>').text(file.error));
        }
        if (index + 1 === data.files.length) {
            data.context.find('button')
                .text('Upload')
                .prop('disabled', !!data.files.error);
        }
    }).on('fileuploadprogressall', function (e, data) {
        var progress = parseInt(data.loaded / data.total * 100, 10);
        $('#progress .progress-bar').css('width', progress + '%');
    }).on('fileuploaddone', function (e, data) {
        // status for the user
        flash('success', data.result.files.length);
        $.each(data.result.files, function (index, file) {
            console.log('DONE file:', index, file);
        });
    }).on('fileuploadfail', function (e, data) {
        // status for the user
        flash('error', data.result.files.length);
        $.each(data.result.files, function (index, file) {
            console.log('ERROR file:', index, file);
        });
    }).prop('disabled', !$.support.fileInput)
        .parent().addClass($.support.fileInput ? undefined : 'disabled');
})(jQuery);
