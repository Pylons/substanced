var grid, data;

// Handle formatting of a clickable item
function AnchorFormatter(row, cell, value, columnDef, dataContext) {
    var url = dataContext['url'];
    return '<a href="' + url + '">' + value + '</a>'
}

var columns = [
    {id:"title", name:"Title", field:"title", width:350,
        formatter:AnchorFormatter},
    {id:"name", name:"Name", field:"name", width:250}
];

var options = {
    enableColumnReorder:false
};

$(function () {
    var json_url = $('.sd_grid').data('json-url');
    $.getJSON(json_url)
        .success(function (data) {
                     grid = new Slick.Grid(".sd_grid", data,
                                           columns, options);
                 });
})
