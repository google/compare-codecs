---
layout: default
title: Results
---
<!-- Scripting stuff -->
<script src="https://www.google.com/jsapi"></script>
<script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>
<!-- Special Javascript for this site -->
<script src="/assets/js/codecfuncs.js"></script>
<h2>{{ page.title }}</h2>

This page shows the results of encodes available on this particular site.

NOTE: All results are fake. They will be generated using Javascript from
JSON-formatted data files in the eventual site.

### No-limit results

This is the result of comparing encodings based on PSNR and file size being
below a certain bitrate, with no restrictions on tools applied, and no
penalty applied for moving bits around within the bitstream.

<!--Note: This table will be overwritten on page load. -->
<div id="basic-results">

|             |        VP8 |        x264 |  H263 |
| ----------- | ---------- | ----------- | ----- |
| VP8         |            |        <a href="/results/generated/vp8-x264.html">-22%</a> | <a href="/results/generated/vp8-h263.html">-71</a> |
| x264        |        <a href="/results/generated/x264-vp8.html">+30%</a> | | <a href="/results/generated/x264-h263.html">-64</a> |
| H263        | <a href="/results/generated/h263-vp8.html">+262</a> | <a href="/results/generated/h263-x264.html">+203</a> | |
{:.td-right}

</div>
<script>
FillInResults('basic-results')
</script>

### Fixed QP results

This table shows the overall numeric results based on PSNR, computed according
to the BD-PSNR method. Click on a percentage to go to the page that shows the
detailed results, and results based on other metrics.


|             | VP8 2-Pass | x264 2-Pass | HEVC-HM |
| ----------- | ---------- | ----------- | ------- |
| VP8 2-pass  |            |        +10% |    -12% |
| x264 2-Pass |        -8% |             |    +17% |
| HEVC-HM     |        -6% |         +7% |         |
{:.td-right}

Note that the table is not symmetric; if A beats B by 12% when A is the
baseline, A will beat B by 8% if B is the baseline. This follows from the way
in which the percentages are computed. (FIXME: Check numbers)


### Fixed bitrate results

This table shows the overall numeric results based on PSNR and bitrate
overrun. The score for any clip is reduced by 0.1 for each second of
accumulated delay, divided by the length of the clip.


|             | VP8 2-Pass | x264 2-Pass | HEVC-HM |
| ----------- | ---------- | ----------- | ------- |
| VP8 2-pass  |            |        +10% |    -12% |
| x264 2-Pass |        -8% |             |    +17% |
| HEVC-HM     |        -6% |         +7% |         |
{:.td-right}


### Interactive Results

This table shows the overall numeric results based on PSNR and bitrate
overrun. The score for any clip is reduced by 1 for each second of accumulated
delay, divided by the length of the clip.

In addition, to qualify for this ranking, an encode must be performed using
less CPU time (single CPU) than the length of the clip, and it must have no
forward looking elements - that is, a decoded frame N must be exactly the same
no matter what the content of the original frame N+1 and later were.


|      | VP8-RT | X264-RT | HEVC-HM |
| ---- | ------ | ------- | ------- |
| VP8  |        |    +10% |     DNQ |
| X264 |    -8% |         |     DNQ |
| HEVC |    DNQ |     DNQ |         |
{:.td-right}
