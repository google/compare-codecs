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

Note that when picking configurations to display in the "best of" charts,
the configuration with the highest score is picked, not the one with the
highest PSNR. Score is displayed in the detailed results.

<div id="heading"></div>

<div id="table-and-graph" style="position: relative">
<div id="infotable" style="float: left; width: 400px; height: 600px"></div>

<div id="metricgraph" style="margin-left: 400px; height:600px"></div>
</div>

<div id="encodinginfo"></div>
<script>
sweepdata = {{ site.data.sweepdata | jsonify }}
</script>
<script>
google.setOnLoadCallback(function() {
  showSweepData(location.search)
});
</script>
