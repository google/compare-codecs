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

### No-limit results

This is the result of comparing encodings based on PSNR and file size being
below a certain bitrate, with no restrictions on tools applied, and no
penalty applied for moving bits around within the bitstream.

The first column gives the baseline codec; the top row gives the codec it
is compared to, and the number gives the change in bitrate between the two
for the same quality metric.

Positive numbers indicate an increase in filesize (left codec is better);
negative numbers indicate a decrease in filesize (top codec is better).

<!--Note: This table will be overwritten on page load.
    It is present to show what the tables will look like. -->
<div id="config-results">

| PLACEHOLDER |        VP8 |        x264 |  H263 |
| ----------- | ---------- | ----------- | ----- |
| VP8         |            |        -22% |  -71% |
| x264        |       +30% |             |  -64% |
| H263        |      +262% |       +203% |       |
{:.td-right}

</div>

### Tuned results listing

This is the same results as above, but this time, we add the ability to
tune the parameters at each data point.

This will show how far it's possible to squeeze the performance of each
codec - "you can't do better than this".

In the graphs linked below, each codec is represented by a dotted line
showing "this is the best we
can do at this target bitrate", and by a solid line showing the result
of running with the single "best" configuration for all bitrates.

<!--Note: This table will be overwritten on page load.
    It is present to show what the tables will look like. -->
<div id="tuned-results">

| PLACEHOLDER |        VP8 |        x264 |  H263 |
| ----------- | ---------- | ----------- | ----- |
| VP8         |            |        -22% |  -71% |
| x264        |       +30% |             |  -64% |
| H263        |      +262% |       +203% |       |
{:.td-right}

</div>

<div style="display: none"> <!-- Hide this part for now -->
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

</div> <!--end of hiding -->

### Interactive Results

This table shows the overall numeric results based on PSNR and bitrate
overrun. The score for any clip is reduced by 1 for each second of accumulated
delay, divided by the length of the clip.

In addition, to qualify for this ranking, an encode must be performed using
less CPU time (single CPU) than the length of the clip, and it must have no
forward looking elements - that is, a decoded frame N must be exactly the same
no matter what the content of the original frame N+1 and later were.

<div id='rt-results'>
| PLACEHOLDER     | VP8-RT | X264-RT | HEVC-HM |
| --------------- | ------ | ------- | ------- |
| VP8             |        |    +10% |     DNQ |
| X264            |    -8% |         |     DNQ |
| HEVC            |    DNQ |     DNQ |         |
{:.td-right}
</div>

<script>
google.setOnLoadCallback(FillInAllTables);
</script>
