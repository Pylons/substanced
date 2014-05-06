var sdi = function() {

    loading_indicator_on = function() {
        $('#sdi-loading-img').css('display', 'inline');
        return true;
    };

    loading_indicator_off = function() {
        $('#sdi-loading-img').css('display', 'none');
        return true;
    };

    return {loading_indicator_on:loading_indicator_on,
            loading_indicator_off:loading_indicator_off};

}();

// bw compat
window.sdi_loading_indicator_on = sdi.loading_indicator_on;
window.sdi_loading_indicator_off = sdi.loading_indicator_off;
