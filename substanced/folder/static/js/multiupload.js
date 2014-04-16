/*jslint unparam: true, regexp: true */
/*global window, jQuery */

+(function($) {
    'use strict';
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
        previewCrop: true
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
                            console.log('iter', dataItem.done, dataItem);
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
        $('#progress .progress-bar').css(
            'width',
            progress + '%'
        );
    }).on('fileuploaddone', function (e, data) {
      console.log('DONE', data.result);
      // Let's display it a status message in case the user clicks cancel.
      $('#messages')
         .empty()
         .append(
             $('<div class="alert alert-success"></div>')
                 .append('1 file uploaded')
                 .append('<button type="button" class="close" data-dismiss="alert">&times;</button>')
         );
        $.each(data.result.files, function (index, file) {
            console.log('DONE file:', index, file);

        });
    }).on('fileuploadfail', function (e, data) {
        $.each(data.result.files, function (index, file) {
            //result.done = true;
            //result.error = true;
            console.log('FAIL file', index, file);
        });

    }).prop('disabled', !$.support.fileInput)
        .parent().addClass($.support.fileInput ? undefined : 'disabled');
})(jQuery);
