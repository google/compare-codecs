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

This page shows the video encoding results available on this particular site.

NOTE: All results (excepte the first table) are fake. They will be
generated using Javascript from
JSON-formatted data files in the eventual site.

### No-limit results

This is the result of comparing encodings based on PSNR and file size being
below a certain bitrate, with no restrictions on tools applied, and no
penalty applied for moving bits around within the bitstream.

The top row gives the baseline codec; the first column gives the codec it
is compared to, and the number gives the change in bitrate between the two
for the same quality metric.

<!--Note: This table will be overwritten on page load.
    It is present to show what the tables will look like. -->
<div id="basic-results">

| PLACEHOLDER |        VP8 |        x264 |  H263 |
| ----------- | ---------- | ----------- | ----- |
| VP8         |            |        -22% |  -71% |
| x264        |       +30% |             |  -64% |
| H263        |      +262% |       +203% |       |
{:.td-right}

</div>
<script>
FillInAllTables()
</script>

### Fixed QP results

This table shows the overall numeric results based on PSNR, computed according
to the BD-PSNR method. Click on a percentage to go to the page that shows the
detailed results, and results based on other metrics.


| PLACEHOLDER | VP8 2-Pass | x264 2-Pass | HEVC-HM |
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


| PLACEHOLDER | VP8 2-Pass | x264 2-Pass | HEVC-HM |
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


| PLACEHOLDER     | VP8-RT | X264-RT | HEVC-HM |
| --------------- | ------ | ------- | ------- |
| VP8             |        |    +10% |     DNQ |
| X264            |    -8% |         |     DNQ |
| HEVC            |    DNQ |     DNQ |         |
{:.td-right}
