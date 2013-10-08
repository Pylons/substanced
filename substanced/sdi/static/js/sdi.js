
(function($) {   // closure

    window.sdi_loading_indicator_on = function() {
        $('#sdi-loading-img').css('display', 'inline');
        return true;
    };

    window.sdi_loading_indicator_off = function() {
        $('#sdi-loading-img').css('display', 'none');
        return true;
    };

})(jQuery);       // end closure
