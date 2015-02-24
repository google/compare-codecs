// Javascript functions for manipulating codec results.
google.load('visualization', '1.0', {'packages':['table', 'corechart']})

// Global variables for the comparision pages.
var better_table = null;  // A gviz table listing the files considered.
var selected_file = 0;
var selected_metric = null;
var encoding_info = null;
var row_to_details = null;  // An array of row-to-details mappings.
var codec_to_encodings = {};

function fetchEncodingInfo() {
  // The parameters are the location.search substring from the query.
  var codec1 = 'vp9';
  var codec2 = 'x264';
  var criterion = 'psnr-single';
  var url = '/assets/gviz-bug-data.json'
  $.ajax({
    url: url,
    dataType: 'json',
  }).done(function(responseObject) {
    // Put the encoding info into a global object.
    encoding_info = responseObject;
    var codec_names = responseObject['codecs'];
    var bettertable = document.getElementById("bettertable");
    // Construct a table with the codecs across, and the file names
    // down. Show relative performance of all codecs but the first one.
    var overall_avg = responseObject['overall']['avg'];
    var overall_drate = responseObject['overall']['drate'];
    var viz_data = new google.visualization.DataTable();
    viz_data.addColumn('string', 'Filename');
    viz_data.addColumn('number', 'Size AVG')
    viz_data.addColumn('number', 'Size DRATE');
    for (var i = 0; i < overall_avg.length; i++) {
      viz_data.addRow([overall_avg[i]['file'],
                      overall_avg[i][codec2],
                      overall_drate[i][codec2]]);
    }
    // Format all PSNR values to 2 digits.
    var formatter = new google.visualization.NumberFormat({fractionDigits: 2});
    formatter.format(viz_data, 1);
    formatter.format(viz_data, 2);
    better_table = new google.visualization.Table(bettertable);
    better_table.draw(viz_data);
  }).fail(function(jqXHR, textStatus, errorThrown) {
    alert('Error ' + textStatus + errorThrown);
  });
}

