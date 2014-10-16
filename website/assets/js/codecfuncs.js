// Javascript functions for manipulating codec results.
google.load('visualization', '1.0', {'packages':['table']})

google.setOnLoadCallback(FillInAllTables);

function FillInAllTables() {
  var tablesAsJson = $.ajax({
    url: '/results/generated/toplevel.json',
    dataType: 'json',
    async: false
  }).responseText;
  var data = new google.visualization.DataTable(tablesAsJson);
  var table = new google.visualization.Table(
    document.getElementById('basic-results'));
  table.draw(data, {allowHtml: true});
}
