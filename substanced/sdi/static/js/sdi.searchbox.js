/* Searchbox in the SDI header, based on Twitter Bootstrap
 * Typeahead */


/*

TODO
- keyUp buffering
- Hide when not logged in
- Change this JS to not be just searchbox?
- Search button at end of field, handle "enter"
- Option to disable LiveSearch if there are too many items
- CQE?

 */

$(document).ready(function () {

    var sb = $('#sdi_searchbox');
    var sb_url = sb.data('sourceurl');
    var server_data = {};

    sb.typeahead(
        {
            minLength:2,
            source:function (query, process) {
                /*

                 The server return a sequence of dicts like:
                 [{'url': 'http://1/', 'label':'Some Title'},]

                 The URL is, of course, the URL and is expected to be
                 unique for each resource. The label is what is shown
                 in the typeahead dropdown. When a user chooses an item,
                 we navigate to the resource. If they press enter in the
                 searchbox while typing, and don't select a result,
                 we go to search results.

                 */
                return $.ajax(
                    {
                        url:sb_url,
                        type:'get',
                        data:{query:query},
                        dataType:'json'
                    })
                    .done(function (json) {
                              $.each(json, function (index, value) {
                                  server_data[value.url] = value.label;
                              })

                              return process(jQuery.map(json, function (val) {
                                  return val.url;
                              }));
                          });
            },
            matcher:function (item) {
                /* Don't do any client-side matching */
                return true;
            },
            updater:function (item) {
                /* Navigate away if the user chooses an item */

                window.location.href = item;
            },
            highlighter:function (item) {
                /* We have the URL as the data-value, get the label */
                var label = server_data[item];
                return $('<span>' + label + '</span>');
            },
            sorter:function (items) {
                /*

                First item is auto selected, which forces the search
                to be exact. Adding the query at the top of the
                results gets around this problem, so we can return a
                result page when there's no exact match

                */
                item_url = sb_url + '?results=1&query=' + this.query;
                server_data[item_url] = this.query;
                items.unshift(sb_url + '?results=1&query=' + this.query);
                return items;
            }
        });
});
