---
layout: default
title: Results for codec pair
---
<!-- Scripting stuff -->
<script src="https://www.google.com/jsapi"></script>
<script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>
<!-- Special Javascript for this site -->
<script src="/assets/js/codecfuncs.js">
</script>
<h2>
{{ page.title }}
</h2>
<!-- Should be appended to title. Formatting problem. -->
Comparing the performance of codecs

<div class="row">
  <div id="heading" class="col-md-12"></div>
</div>
<div class="row" id="table-and-graph">
  <div class="col-md-6"><div id="bettertable"></div></div>
  <div class="col-md-6" id="metricgraph" style="height:600px"></div>

</div>
<div class="row">
  <div class="col-md-12" id="encodinginfo"></div>
  <a id="sweepdatalink" style="visibility: hidden">
     More information about encodings used
  </a>
</div>

<script>
google.setOnLoadCallback(function() {
  fetchEncodingInfo(location.search)
});
</script>
