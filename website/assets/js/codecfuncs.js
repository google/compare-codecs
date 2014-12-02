// Javascript functions for manipulating codec results.
google.load('visualization', '1.0', {'packages':['table']})

google.setOnLoadCallback(FillInAllTables);

function FillInOneTable(url, id) {
  var tablesAsJson = $.ajax({
    url: url,
    dataType: 'json',
    async: false
  }).responseText;
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
  var data = new google.visualization.DataTable(tablesAsJson);
  var table = new google.visualization.Table(
    document.getElementById(id));
  table.draw(data, tableStyles);
}

function FillInAllTables() {
  FillInOneTable('/results/generated/toplevel-psnr.json', 'basic-results')
  FillInOneTable('/results/generated/toplevel-rt.json', 'rt-results')
}
