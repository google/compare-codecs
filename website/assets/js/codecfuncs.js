// Javascript functions for manipulating codec results.
google.load('visualization', '1.0', {'packages':['table', 'corechart']})

// Global variables for the comparision pages.
var better_table = null;  // A gviz table listing the files considered.
var selected_file = null;
var selected_metric = null;
var encoding_info = null;
var row_to_details = null;  // An array of row-to-details mappings.

function FillInOneTable(url, id) {
  $.ajax({
    url: url,
    dataType: 'json',
  }).done(function(responseText) {
    var tableStyles = { allowHtml: true,
                      alternatingRowStyle: false,
                      showRowNumber: false,
                      sort: 'disable',
                      // Width is problematic, cross-device.
                      width: '50%',
                      cssClassNames: {
                        // These map to .rslts-* classes
                        headerRow: 'rslts-headerRow',
                        tableRow: 'rslts-tableRow',
                        oddTableRow: 'rslts-oddTableRow',
                        selectedTableRow: 'rslts-selectedTableRow',
                        hoverTableRow: 'rslts-hoverTableRow',
                        headerCell: 'rslts-headerCell',
                        tableCell: 'rslts-tableCell',
                        rowNumberCell: 'rslts-rowNumberCell',
                      }
                    };
    var data = new google.visualization.DataTable(responseText);
    var table = new google.visualization.Table(
    document.getElementById(id));
    table.draw(data, tableStyles);
  })
}

function FillInAllTables() {
  FillInOneTable('/results/generated/toplevel-psnr.json', 'basic-results')
  FillInOneTable('/results/generated/toplevel-rt.json', 'rt-results')
}

function ParseParameters(parameters) {
  var param_list = {};
  var parts = parameters.substring(1).split('&');
  for (var i = 0; i < parts.length; i++) {
    var name_value = parts[i].split('=');
    if (!name_value[0]) { continue; }
    param_list[name_value[0]] = name_value[1] || true;
  }
  return param_list;
}


function fetchEncodingInfo(parameters) {
  // The parameters are the location.search substring from the query.
  var param_list = ParseParameters(parameters);
  var codec1 = param_list['codec1'];
  var codec2 = param_list['codec2'];
  var criterion = param_list['criterion'];
  var document_name = codec1 + '-' + codec2 +
      '-' + criterion + '.json';
  var url = '/results/generated/' + document_name;
  $.ajax({
    url: url,
    dataType: 'json',
  }).done(function(responseObject) {
    // Put the encoding info into a global object.
    encoding_info = responseObject;
    var heading = document.getElementById("heading");
    var codec_names = responseObject['codecs'];
    heading.innerHTML = codec_names[0][1] + ' and ' + codec_names[1][1] +
      ' on criterion ' + criterion;
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
    better_table = new google.visualization.Table(bettertable);
    better_table.draw(viz_data);
    google.visualization.events.addListener(better_table, 'select',
                                            selectBetterHandler);
    displayGraph(overall_avg[0]['file']);
  }).fail(function(jqXHR, textStatus, errorThrown) {
    alert('Error ' + textStatus + errorThrown);
  });
}

function selectBetterHandler() {
  var selection = better_table.getSelection();
  for (var i = 0; i < selection.length; i++) {
    item = selection[i];
  }
  selected_file = item.row;

  displayGraph(encoding_info['overall']['avg'][selected_file]['file']);
}

function displayGraph(filename) {
  var graph_area = document.getElementById('metricgraph');
  var chart = new google.visualization.ScatterChart(graph_area);
  var metricdata = new google.visualization.DataTable();
  var metricview = new google.visualization.DataView(metricdata);
  var codec1 = encoding_info['codecs'][0][0];
  var codec2 = encoding_info['codecs'][1][0];
  var detailed_1 = encoding_info['detailed'][codec1][filename];
  var detailed_2 = encoding_info['detailed'][codec2][filename];
  metricdata.addColumn('number', 'bitrate');
  metricdata.addColumn('number', codec1);
  metricdata.addColumn('number', codec2);
  // Store a global mapping of row number to result.
  row_to_details = [];
  for (var i = 0; i < detailed_1.length; i++) {
    var result = detailed_1[i]['result'];
    metricdata.addRow([result['bitrate'], result['psnr'], null]);
    row_to_details.push(detailed_1[i]);
  }
  for (var i = 0; i < detailed_2.length; i++) {
    var result = detailed_2[i]['result'];
    metricdata.addRow([result['bitrate'], null, result['psnr']]);
    row_to_details.push(detailed_2[i]);
  }
  chart.draw(metricdata, {curveType:'function',
      chartArea:{left:60, top:6, width:"100%", height:"80%"},
      hAxis:{title:"datarate in kbps"},
      vAxis:{title:"quality in decibels"},
      legend:{position:"in"},
      title:"chart-title",
      pointSize:2,
      lineWidth:1,
      width:"100%",
      height:"80%" });

  google.visualization.events.addListener(chart, 'onmouseover', chartMouseOver);

}

function chartMouseOver(e) {
  displayDetailsOnEncoding(e.row);
}

function displayDetailsOnEncoding(row_number) {
  var area = document.getElementById('encodinginfo');
  area.innerHTML = '<pre>' +
      JSON.stringify(row_to_details[row_number], null, 2) +
      '</pre>';
}
