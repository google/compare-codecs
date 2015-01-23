// Javascript functions for manipulating codec results.
google.load('visualization', '1.0', {'packages':['table', 'corechart']})

// Global variables for the comparision pages.
var better_table = null;  // A gviz table listing the files considered.
var selected_file = 0;
var selected_metric = null;
var encoding_info = null;
var row_to_details = null;  // An array of row-to-details mappings.
var codec_to_encodings = {};
var evaluation_criterion = '';
var metric_units = {
  'score': 'Score - decibels',
  'psnr': 'Quality in decibels PSNR',
  'encode_cputime': 'Encode CPU time in seconds'
};

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

function FillInAllTablesNew() {
  FillInOneTable('/results/generated/toplevel-psnr-new.json', 'basic-results')
  FillInOneTable('/results/generated/toplevel-rt-new.json', 'rt-results')
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
  // Make criterion available globally.
  evaluation_criterion = criterion;
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
    // Format all PSNR values to 2 digits.
    var formatter = new google.visualization.NumberFormat({fractionDigits: 2});
    formatter.format(viz_data, 1);
    formatter.format(viz_data, 2);
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
  // Select the last item in the selection.
  item = selection[selection.length-1];
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
  codec_to_encodings[codec1] = {};
  codec_to_encodings[codec2] = {};
  // Note all the encodings used for each codec (for linking).
  for (var i = 0; i < detailed_1.length; i++) {
    codec_to_encodings[codec1][detailed_1[i]['config_id']] = 1;
  }
  for (var i = 0; i < detailed_2.length; i++) {
    codec_to_encodings[codec2][detailed_2[i]['config_id']] = 1;
  }
  // TODO(hta): Call displayGraphLines instead of code below.
  metricdata.addColumn('number', 'bitrate');
  metricdata.addColumn('number', codec1);
  metricdata.addColumn('number', codec2);
  // Store a global mapping of row number to result.
  row_to_details = [];
  for (var i = 0; i < detailed_1.length; i++) {
    var result = detailed_1[i]['result'];
    metricdata.addRow([result['bitrate'], result['psnr'], null]);
    detailed_1[i]['codec'] = codec1
    row_to_details.push(detailed_1[i]);
  }
  for (var i = 0; i < detailed_2.length; i++) {
    var result = detailed_2[i]['result'];
    metricdata.addRow([result['bitrate'], null, result['psnr']]);
    detailed_2[i]['codec'] = codec2
    row_to_details.push(detailed_2[i]);
  }
  chart.draw(metricdata, {curveType:'function',
      chartArea:{left:60, top:6, width:"100%", height:"80%"},
      hAxis:{title:"datarate in kbps"},
      vAxis:{title: metric_units['psnr']},
      legend:{position:"in"},
      title:"chart-title",
      pointSize:2,
      lineWidth:1,
      width:"100%",
      height:"800px" });

  google.visualization.events.addListener(chart, 'onmouseover', chartMouseOver);

}

function displayGraphLines(result_array, metric) {
  var graph_area = document.getElementById('metricgraph');
  var chart = new google.visualization.ScatterChart(graph_area);
  var metricdata = new google.visualization.DataTable();
  var metricview = new google.visualization.DataView(metricdata);
  metricdata.addColumn('number', 'bitrate');
  var number_of_lines = result_array.length
  for (var i = 0; i < result_array.length; i++) {
    metricdata.addColumn('number', i);
  }
  // Populate rows.
  // Also store a global mapping of row number to result,
  // which is used by the mouseover function.
  row_to_details = [];
  for (var i = 0; i < result_array.length; i++) {
    detailed = result_array[i];
    for (var j = 0; j < detailed.length; j++) {
      var result = detailed[j]['result'];
      var row = new Array(number_of_lines + 1);
      row[0] = result['bitrate'];
      if (metric in detailed[j]) {
        row[i+1] = detailed[j][metric];
      } else {
        row[i+1] = result[metric];
      }
      metricdata.addRow(row);
      row_to_details.push(detailed[j]);
    }
  }
  chart.draw(metricdata, {curveType:'function',
      chartArea:{left:60, top:6, width:"100%", height:"80%"},
      hAxis:{title:"datarate in kbps"},
      vAxis:{title: metric_units[metric]},
      legend:{position:"in"},
      title:"chart-title",
      pointSize:2,
      lineWidth:1,
      width:"100%",
      height:"800px" });

  google.visualization.events.addListener(chart, 'onmouseover', chartMouseOver);
}

function chartMouseOver(e) {
  // Under certain circumstances, e.row is "null".
  if (typeof e.row == 'number') {
    displayDetailsOnEncoding(e.row);
  }
}

function displayDetailsOnEncoding(row_number) {
  var area = document.getElementById('encodinginfo');
  var details = row_to_details[row_number]
  area.innerHTML =
      '<dl>' +
      '<dt>Configuration ID: <dd>' + details['config_id'] +
      '<dt>Score: <dd>' + details['score'] +
      '<dt>Encode command: <dd>' + details['encode_command'] +
      '<dt>Results:<dd><pre>' +
      JSON.stringify(details['result'], null, 2) +
      '</pre></dl>';
  // Update the "more info" link with the right data (if present).
  sweeplink = document.getElementById('sweepdatalink');
  if (sweeplink) {
    var filename = encoding_info['overall']['avg'][selected_file]['file'];
    sweeplink.href = '/results/sweepdata.html?codec=' + details['codec']
      + '&filename=' + filename
      + '&criterion=' + evaluation_criterion
      + '&configs=' + Object.keys(codec_to_encodings[details['codec']]).join(',');
    sweeplink.style.visibility = "visible";
  }
}

function showSweepData(parameters, metric) {
  var param_list = ParseParameters(parameters);
  var codec = param_list['codec'];
  var criterion = param_list['criterion'];
  var filename = param_list['filename'];
  var configs = param_list['configs'].split(',');
  // We assume that sweep data is the global variable "sweepdata".
  var config_data_list = sweepdata['sweepdata'][codec][filename]
  var list_to_show = [];
  for (var i = 0; i < configs.length; i++) {
    list_to_show.push(config_data_list[configs[i]]);
  }
  displayGraphLines(list_to_show, metric);

  infotable = document.getElementById('infotable');
  infotable.innerHTML = '<p>Codec: ' + codec + '<p>Filename: ' + filename +
    '<p>Metric graphed: ' + metric;
  for (var i = 0; i < configs.length; i++) {
    var para = '<p>' + configs[i];
    para += ' - ' + sweepdata['sweepdata'][codec][filename][configs[i]].length + ' encodings</p>';
    infotable.innerHTML += para;
  }
}
