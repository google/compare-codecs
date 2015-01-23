---
layout: default
title: Data for a number of codec configurations
---
<!-- Scripting stuff -->
<script src="https://www.google.com/jsapi"></script>
<script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>
<!-- Special Javascript for this site -->
<script src="/assets/js/codecfuncs.js"></script>
<h2>
{{ page.title }}
</h2>
This graph shows the PSNR/size of a number of related configurations.

Mouse over the points on the chart to see the command lines used and the
detailed results for each encoding.

Use the buttons at bottom to pick which metric is graphed.

<div id="heading"></div>

<div class="row" id="table-and-graph">
  <div class="col-md-6" id="infotable"></div>
  <div class="col-md-6" id="metricgraph" style="height:600px"></div>
</div>
<div class="row" id="encodinginfo"></div>
<script>
sweepdata = {{ site.data.sweepdata | jsonify }}
</script>
<input type="button" value="PSNR"
 onclick="showSweepData(location.search, 'psnr')">
<input type="button" value="Score"
 onclick="showSweepData(location.search, 'score')">
<input type="button" value="Encode CPU time"
 onclick="showSweepData(location.search, 'encode_cputime')">
<script>
google.setOnLoadCallback(function() {
  showSweepData(location.search, 'psnr');
});
</script>
