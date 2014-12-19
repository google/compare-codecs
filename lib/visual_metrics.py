#!/usr/bin/python
# Copyright 2014 Google.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Converts video encoding result data from text files to visualization
data source."""

__author__ = "jzern@google.com (James Zern),"
__author__ += "jimbankoski@google.com (Jim Bankoski)"
__author__ += "hta@gogle.com (Harald Alvestrand)"


import encoder
import gviz_api
import math
import mpeg_settings
import numpy
import optimizer
import re
import string
import pick_codec


def bdsnr(metric_set1, metric_set2):
  """
  BJONTEGAARD    Bjontegaard metric calculation
  Bjontegaard's metric allows to compute the average gain in psnr between two
  rate-distortion curves [1].
  rate1,psnr1 - RD points for curve 1
  rate2,psnr2 - RD points for curve 2

  returns the calculated Bjontegaard metric 'dsnr'

  code adapted from code written by : (c) 2010 Giuseppe Valenzise
  http://www.mathworks.com/matlabcentral/fileexchange/27798-bjontegaard-metric/content/bjontegaard.m
  """
  rate1 = [x[0] for x in metric_set1]
  psnr1 = [x[1] for x in metric_set1]
  rate2 = [x[0] for x in metric_set2]
  psnr2 = [x[1] for x in metric_set2]

  log_rate1 = map(math.log, rate1)
  log_rate2 = map(math.log, rate2)

  # Best cubic poly fit for graph represented by log_ratex, psrn_x.
  p1 = numpy.polyfit(log_rate1, psnr1, 3)
  p2 = numpy.polyfit(log_rate2, psnr2, 3)

  # Integration interval.
  min_int = max([min(log_rate1), min(log_rate2)])
  max_int = min([max(log_rate1), max(log_rate2)])

  # Integrate p1, and p2.
  p_int1 = numpy.polyint(p1)
  p_int2 = numpy.polyint(p2)

  # Calculate the integrated value over the interval we care about.
  int1 = numpy.polyval(p_int1, max_int) - numpy.polyval(p_int1, min_int)
  int2 = numpy.polyval(p_int2, max_int) - numpy.polyval(p_int2, min_int)

  # Calculate the average improvement.
  avg_diff = (int2 - int1) / (max_int - min_int)
  return avg_diff

def bdrate(metric_set1, metric_set2):
  """
  BJONTEGAARD    Bjontegaard metric calculation
  Bjontegaard's metric allows to compute the average % saving in bitrate
  between two rate-distortion curves [1].

  rate1,psnr1 - RD points for curve 1
  rate2,psnr2 - RD points for curve 2

  adapted from code from: (c) 2010 Giuseppe Valenzise

  """
  rate1 = [x[0] for x in metric_set1]
  psnr1 = [x[1] for x in metric_set1]
  rate2 = [x[0] for x in metric_set2]
  psnr2 = [x[1] for x in metric_set2]

  log_rate1 = map(math.log, rate1)
  log_rate2 = map(math.log, rate2)

  # Best cubic poly fit for graph represented by log_ratex, psrn_x.
  p1 = numpy.polyfit(psnr1, log_rate1, 3)
  p2 = numpy.polyfit(psnr2, log_rate2, 3)

  # Integration interval.
  min_int = max([min(psnr1), min(psnr2)])
  max_int = min([max(psnr1), max(psnr2)])

  # find integral
  p_int1 = numpy.polyint(p1)
  p_int2 = numpy.polyint(p2)

  # Calculate the integrated value over the interval we care about.
  int1 = numpy.polyval(p_int1, max_int) - numpy.polyval(p_int1, min_int)
  int2 = numpy.polyval(p_int2, max_int) - numpy.polyval(p_int2, min_int)

  # Calculate the average improvement.
  avg_exp_diff = (int2 - int1) / (max_int - min_int)

  # In really bad formed data the exponent can grow too large.
  # clamp it.
  if avg_exp_diff > 200 :
    avg_exp_diff = 200

  # Convert to a percentage.
  avg_diff = (math.exp(avg_exp_diff) - 1) * 100

  return avg_diff


def FillForm(string_for_substitution, dictionary_of_vars):
  """
  This function substitutes all matches of the command string //%% ... %%//
  with the variable represented by ...  .
  """
  return_string = string_for_substitution
  for i in re.findall("//%%(.*)%%//", string_for_substitution):
    return_string = re.sub("//%%" + i + "%%//", dictionary_of_vars[i],
                           return_string)
  return return_string


def HasMetrics(line):
  """
  The metrics files produced by vpxenc are started with a B for headers.
  """
  if line[0:1] != "B" and len(string.split(line))>0:
    return True
  return False


def ParseMetricFile(file_name, metric_column):
  """
  Convert a metrics file into a set of numbers.
  This returns a sorted list of tuples with the first number
  being from the first column (bitrate) and the second being from
  metric_column (counting from 0).
  """
  metric_set1 = set([])
  metric_file = open(file_name, "r")
  for line in metric_file:
    metrics = string.split(line)
    if HasMetrics(line):
      if metric_column < len(metrics):
        my_tuple = float(metrics[0]), float(metrics[metric_column])
      else:
        my_tuple = float(metrics[0]), 0
      metric_set1.add(my_tuple)
  metric_set1_sorted = sorted(metric_set1)
  return metric_set1_sorted


def GraphBetter(metric_set1_sorted, metric_set2_sorted, use_set2_as_base):
  """
  Search through the sorted metric set for metrics on either side of
  the metric from file 1.  Since both lists are sorted we really
  should not have to search through the entire range, but these
  are small lists."""
  total_bitrate_difference_ratio = 0.0
  count = 0
  # TODO(hta): Replace whole thing with a call to numpy.interp()
  for bitrate, metric in metric_set1_sorted:
    for i in range(len(metric_set2_sorted) - 1):
      s2_bitrate_0, s2_metric_0 = metric_set2_sorted[i]
      s2_bitrate_1, s2_metric_1 = metric_set2_sorted[i + 1]
      # We have a point on either side of our metric range.
      if s2_metric_0 < metric <= s2_metric_1:
        # Calculate a slope.
        if s2_metric_1 - s2_metric_0 != 0:
          metric_slope = ((s2_bitrate_1 - s2_bitrate_0) /
                          (s2_metric_1 - s2_metric_0))
        else:
          metric_slope = 0

        estimated_s2_bitrate = (s2_bitrate_0 + (metric - s2_metric_0) *
                                metric_slope)

        # Calculate percentage difference as given by base.
        if use_set2_as_base:
          bitrate_difference_ratio = ((bitrate - estimated_s2_bitrate) /
                                        estimated_s2_bitrate)
        else:
          bitrate_difference_ratio = ((bitrate - estimated_s2_bitrate) /
                                      bitrate)

        total_bitrate_difference_ratio += bitrate_difference_ratio
        count += 1
        break

  # Calculate the average improvement between graphs.
  if count != 0:
    avg = total_bitrate_difference_ratio / count

  else:
    avg = 0.0

  return avg

def DataSetBetter(metric_set1, metric_set2, method):
  """
  Compares two data sets and determines which is better and by how
  much.
  The input metric set is sorted on bitrate.
  """
  # Be fair to both graphs by testing all the points in each.
  if method == 'avg':
    avg_improvement = 50 * (
                       GraphBetter(metric_set1, metric_set2,
                                   use_set2_as_base=True) -
                       GraphBetter(metric_set2, metric_set1,
                                   use_set2_as_base=False))
  elif method == 'dsnr':
    avg_improvement = bdsnr(metric_set1, metric_set2)
  else:
    avg_improvement = bdrate(metric_set2, metric_set1)

  return avg_improvement


def FileBetter(file_name_1, file_name_2, metric_column, method):
  """
  Compares two data files and determines which is better and by how
  much.
  metric_column is the metric.
  """
  # Store and parse our two files into lists of unique tuples.

  # Read the two files, parsing out lines starting with bitrate.
  metric_set1_sorted = ParseMetricFile(file_name_1, metric_column)
  metric_set2_sorted = ParseMetricFile(file_name_2, metric_column)

  return DataSetBetter(metric_set1_sorted, metric_set2_sorted, method)


def HtmlPage(page_template, page_title="", page_subtitle="",
             filestable="", snrs="", formatters=""):
  """
  Creates a HTML page from the template and variables passed to it.
  """
  # Build up a dictionary of the variables actually used in the template.
  my_dict = {
    'page_title': page_title,
    'page_subtitle': page_subtitle,
    'filestable_dpsnr': filestable['dsnr'],
    'filestable_avg': filestable['avg'],
    'filestable_drate': filestable['drate'],
    'snrs': snrs,
    'formatters': formatters
    }
  return FillForm(page_template, my_dict)


def ListOneTarget(codecs, rate, videofile, do_score, datatable,
                  score_function=None, full_results=False):
  """Extend a datatable with the info about one video file's scores."""
  for codec_name in codecs:
    # For testing:
    # Allow for direct context injection rather than picking by name.
    if isinstance(codec_name, basestring):
      codec = pick_codec.PickCodec(codec_name)
      my_optimizer = optimizer.Optimizer(codec, score_function=score_function)
    else:
      my_optimizer = codec_name
      codec_name = my_optimizer.context.codec.name
    bestsofar = my_optimizer.BestEncoding(rate, videofile)
    if do_score and not bestsofar.Result():
      bestsofar.Execute()
      bestsofar.Store()
    assert(bestsofar.Result())
    # Ignore results that score less than zero.
    if my_optimizer.Score(bestsofar) < 0.0:
      return
    if full_results:
      (datatable.setdefault(codec_name, {})
          .setdefault(videofile.basename, [])
          .append({'target_bitrate': rate,
                   'score': my_optimizer.Score(bestsofar),
                   'result': bestsofar.ResultWithoutFrameData()}))
    else:
      (datatable.setdefault(codec_name, {})
          .setdefault(videofile.basename, [])
          .append((bestsofar.result['bitrate'], bestsofar.result['psnr'])))


def ListMpegResults(codecs, do_score, datatable, score_function=None,
                    full_results=False):
  """List all scores for all tests in the MPEG test set for a set of codecs."""
  # It is necessary to sort on target bitrate in order for graphs to display
  # correctly.
  for rate, filename in sorted(mpeg_settings.MpegFiles().AllFilesAndRates()):
    videofile = encoder.Videofile(filename)
    ListOneTarget(codecs, rate, videofile, do_score, datatable,
                  score_function, full_results)


def ExtractBitrateAndPsnr(datatable, codec, filename, full_results=False):
  if full_results:
    dataset = [(r['result']['bitrate'], r['result']['psnr'])
                          for r in datatable[codec][filename]]
  else:
    dataset = datatable[codec][filename]
  return dataset


def BuildComparisionTable(datatable, metric, baseline_codec, other_codecs,
                          full_results=False):
  """Builds a table of comparision data for this metric."""


  # Find the metric files in the baseline codec.
  videofile_name_list = datatable[baseline_codec].keys()

  countoverall = {}
  sumoverall = {}

  for this_codec in other_codecs:
    countoverall[this_codec] = 0
    sumoverall[this_codec] = 0

  # Data holds the data for the visualization, name given comes from
  # gviz_api sample code.
  data = []
  for filename in videofile_name_list:
    row = {'file': filename }
    baseline_dataset = ExtractBitrateAndPsnr(datatable,
                                             baseline_codec,
                                             filename,
                                             full_results)
    # Read the metric file from each of the directories in our list.
    for this_codec in other_codecs:

      # If there is a metric in this_codec,
      # calculate the overall difference between it and the baseline
      # codec's metric
      if (this_codec in datatable and filename in datatable[this_codec]
          and filename in datatable[baseline_codec]):
        this_dataset = ExtractBitrateAndPsnr(datatable,
                                             this_codec,
                                             filename,
                                             full_results)
        overall = DataSetBetter(
          baseline_dataset, this_dataset, metric)
        row[this_codec] = overall

        sumoverall[this_codec] += overall
        countoverall[this_codec] += 1

    data.append(row)

  # Add the overall numbers.
  row = {"file": "OVERALL " + metric}
  for this_codec in other_codecs:
    if countoverall[this_codec]:
      row[this_codec] = sumoverall[this_codec] / countoverall[this_codec]
  data.append(row)
  return data

def BuildGvizDataTable(datatable, metric, baseline_codec, other_codecs):
  """Builds a Gviz DataTable giving this metric for the files and codecs"""

  description = {"file": ("string", "File")}
  data = BuildComparisionTable(datatable, metric, baseline_codec, other_codecs)
  for this_codec in other_codecs:
    description[this_codec] = ("number", this_codec)
  # Generate the gViz table
  gviz_data_table = gviz_api.DataTable(description)
  gviz_data_table.LoadData(data)
  return gviz_data_table

def CrossPerformanceGvizTable(datatable, metric, codecs, criterion):
  """Build a square table of codecs and relative performance."""
  videofile_name_list = datatable[codecs[0]].keys()

  description = {}
  description['codec'] = ('string', 'Codec')
  data = []
  for codec in codecs:
    description[codec] = ('string', codec)
  for codec1 in codecs:
    lineitem = {'codec': codec1}
    for codec2 in codecs:
      if codec1 != codec2:
        count = 0
        overall = 0.0
        for filename in videofile_name_list:
          if (codec1 in datatable and filename in datatable[codec1]
              and codec2 in datatable and filename in datatable[codec2]):
            overall += DataSetBetter(
              datatable[codec1][filename],
              datatable[codec2][filename], metric)
            count += 1
        if count > 0:
          display = '<a href=/results/generated/%s-%s-%s.html>%5.2f</a>' % (
            codec1, codec2, criterion, overall / count)
          lineitem[codec2] = (overall / count, display)
    data.append(lineitem)

  gviz_data_table = gviz_api.DataTable(description)
  gviz_data_table.LoadData(data)
  return gviz_data_table
