---
layout: default
title: Results
---

<h2>{{ page.title }}</h2>

This page shows the results of encodes available on this particular site.

NOTE: All results are fake. They will be generated using Javascript from
JSON-formatted data files in the eventual site.


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
