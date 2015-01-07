---
layout: default
title: Results for codec pair
---
<!-- Scripting stuff -->
<script src="https://www.google.com/jsapi"></script>
<script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>
<!-- Special Javascript for this site -->
<script src="/assets/js/codecfuncs.js"></script>
<h2>
{{ page.title }}
</h2>
<!-- Should be appended to title. Formatting problem. -->
Comparing the performance of codecs

<div id="heading"></div>

<div id="table-and-graph" style="position: relative">
<div id="bettertable" style="float: left; width: 400px; height: 600px"></div>

<div id="metricgraph" style="margin-left: 400px; height:600px"></div>
</div>

<div id="encodinginfo"></div>

<script>
google.setOnLoadCallback(function() {
  fetchEncodingInfo(location.search)
});
</script>
