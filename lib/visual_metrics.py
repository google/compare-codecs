#!/usr/bin/python
#
# Copyright 2010 Google Inc.
# All Rights Reserved.

"""Converts video encoding result data from text files to visualization
data source."""

__author__ = "jzern@google.com (James Zern),"
__author__ += "jimbankoski@google.com (Jim Bankoski)"

import fnmatch
import numpy
import os
import re
import string
import sys
import math

import gviz_api

from os.path import basename
from os.path import splitext

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

  log_rate1 = map(lambda x: math.log(x), rate1)
  log_rate2 = map(lambda x: math.log(x), rate2)

  # Best cubic poly fit for graph represented by log_ratex, psrn_x.
  p1 = numpy.polyfit(log_rate1, psnr1, 3)
  p2 = numpy.polyfit(log_rate2, psnr2, 3)

  # Integration interval.
  min_int = max([min(log_rate1),min(log_rate2)])
  max_int = min([max(log_rate1),max(log_rate2)])

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

  log_rate1 = map(lambda x: math.log(x), rate1)
  log_rate2 = map(lambda x: math.log(x), rate2)

  # Best cubic poly fit for graph represented by log_ratex, psrn_x.
  p1 = numpy.polyfit(psnr1, log_rate1, 3)
  p2 = numpy.polyfit(psnr2, log_rate2, 3)

  # Integration interval.
  min_int = max([min(psnr1),min(psnr2)])
  max_int = min([max(psnr1),max(psnr2)])

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
  being from the first column (bitrate) and the second being from metric_column (counting from 0).
  """
  metric_set1 = set([])
  metric_file = open(file_name, "r")
  for line in metric_file:
    metrics = string.split(line)
    if HasMetrics(line):
      if metric_column < len(metrics):
        tuple = float(metrics[0]), float(metrics[metric_column])
      else:
        tuple = float(metrics[0]), 0
      metric_set1.add(tuple)
  metric_set1_sorted = sorted(metric_set1)
  return metric_set1_sorted


def GraphBetter(metric_set1_sorted, metric_set2_sorted, use_set2_as_base):
  """
  Search through the sorted metric file for metrics on either side of
  the metric from file 1.  Since both lists are sorted we really
  should not have to search through the entire range, but these
  are small files."""
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
                       GraphBetter(metric_set1, metric_set2, use_set2_as_base=True) -
                       GraphBetter(metric_set2, metric_set1, use_set2_as_base=False))
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


def HtmlPage(page_template, filestable, snrs, formatters):
  """
  Creates a HTML page from the template and variables passed to it.
  """
  # Build up a dictionary of the five variables actually used in the template.
  dict = {
    'filestable_dpsnr': filestable['dsnr'],
    'filestable_avg': filestable['avg'],
    'filestable_drate': filestable['drate'],
    'snrs': snrs,
    'formatters': formatters
    }
  return FillForm(page_template, dict)


def HandleFiles(variables):
  """
  This script creates html for displaying metric data produced from data
  in a video stats file,  as created by the WEBM project when enable_psnr
  is turned on:

  Usage: visual_metrics.py template.html pattern base_dir sub_dir [ sub_dir2 ..]

  The script parses each metrics file [see below] that matches the
  statfile_pattern  in the baseline directory and looks for the file that
  matches that same file in each of the sub_dirs, and compares the resultant
  metrics bitrate, avg psnr, glb psnr, and ssim. "

  It provides a table in which each row is a file in the line directory,
  and a column for each subdir, with the cells representing how that clip
  compares to baseline for that subdir.   A graph is given for each which
  compares filesize to that metric.  If you click on a point in the graph it
  zooms in on that point.

  a SAMPLE metrics file:

  Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
   25.911   38.242   38.104   38.258   38.121   75.790    14103
  Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
   49.982   41.264   41.129   41.255   41.122   83.993    19817
  Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
   74.967   42.911   42.767   42.899   42.756   87.928    17332
  Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
  100.012   43.983   43.838   43.881   43.738   89.695    25389
  Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
  149.980   45.338   45.203   45.184   45.043   91.591    25438
  Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
  199.852   46.225   46.123   46.113   45.999   92.679    28302
  Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
  249.922   46.864   46.773   46.777   46.673   93.334    27244
  Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
  299.998   47.366   47.281   47.317   47.220   93.844    27137
  Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
  349.769   47.746   47.677   47.722   47.648   94.178    32226
  Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
  399.773   48.032   47.971   48.013   47.946   94.362    36203

  sample use:
  visual_metrics.py template.html "*stt" vp8 vp8b vp8c > metrics.html
  """

  template_file_name = variables[1]

  # This is the path match pattern for finding stats files amongst
  # all the other files it could be.  eg: *.stt
  file_pattern = variables[2]

  # This is the directory with files that we will use to do the comparison
  # against.
  baseline_dir = variables[3]

  # Dirs is directories after the baseline to compare to the base.
  dirs = variables[4:len(variables)]

  snrs = ''
  filestable = {}
  filestable['dsnr'] = ''
  filestable['drate'] = ''
  filestable['avg'] = ''

  # Go through each metric in the list.
  for column in range(1,2):

    # Find the metric files in the baseline directory.
    dir_list = sorted(fnmatch.filter(os.listdir(baseline_dir), file_pattern))

    for metric in ['avg','dsnr','drate']:
      description = {"file": ("string", "File")}

      # Go through each directory and add a column header to our description.
      countoverall = {}
      sumoverall = {}

      for directory in dirs:
        description[directory] = ("number", basename(directory))
        countoverall[directory] = 0
        sumoverall[directory] = 0

      # Data holds the data for the visualization, name given comes from
      # gviz_api sample code.
      data = []
      for filename in dir_list:
        row = {'file': splitext(basename(filename))[0] }
        baseline_file_name = baseline_dir + "/" + filename

        # Read the metric file from each of the directories in our list.
        for directory in dirs:
          metric_file_name = directory + "/" + filename

          # If there is a metric file in the current directory, open it
          # and calculate its overall difference between it and the baseline
          # directory's metric file.
          if os.path.isfile(metric_file_name):
            overall = FileBetter(baseline_file_name, metric_file_name,
                                 column, metric)
            row[directory] = overall

            sumoverall[directory] += overall
            countoverall[directory] += 1

        data.append(row)

      # Add the overall numbers.
      row = {"file": "OVERALL " + metric}
      for directory in dirs:
        if countoverall[directory]:
          row[directory] = sumoverall[directory] / countoverall[directory]
        data.append(row)

      # write the tables out
      data_table = gviz_api.DataTable(description)
      data_table.LoadData(data)

      filestable[metric] = ( filestable[metric] + "filestable_" + metric +
                             "[" + str(column) + "]=" + data_table.ToJSon()
                             + "\n" )

    # Now we collect all the data for all the graphs.  First the column
    # headers which will be Datarate and then each directory.
    columns = ("datarate", baseline_dir)
    description = {"datarate":("number", "Datarate")}
    for directory in dirs:
      description[directory] = ("number", basename(directory))

    description[baseline_dir] = ("number", basename(baseline_dir))

    snrs = snrs + "snrs[" + str(column) + "] = ["

    # Now collect the data for the graphs, file by file.
    for filename in dir_list:

      data = []

      # Collect the file in each directory and store all of its metrics
      # in the associated gviz metrics table.
      all_dirs = dirs + [baseline_dir]
      for directory in all_dirs:

        metric_file_name = directory + "/" + filename
        if not os.path.isfile(metric_file_name):
          continue

        # Read and parse the metrics file storing it to the data we'll
        # use for the gviz_api.Datatable.
        metrics = ParseMetricFile(metric_file_name, column)
        for bitrate, metric in metrics:
          data.append({"datarate": bitrate, directory: metric})

      data_table = gviz_api.DataTable(description)
      data_table.LoadData(data)
      snrs = snrs + "'" + data_table.ToJSon(
         columns_order=tuple(["datarate",baseline_dir]+dirs)) + "',"

    snrs = snrs + "]\n"

    formatters = ""
    for i in range(len(dirs)):
      formatters = "%s   formatter.format(better, %d);" % (formatters, i+1)

  # The template file is the html file into which we will write the
  # data from the stats file, formatted correctly for the gviz_api.
  template_file = open(template_file_name, "r")
  page_template = template_file.read()
  template_file.close()

  print HtmlPage(page_template, filestable, snrs, formatters)
  return

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print HandleFiles.__doc__
  else:
    HandleFiles(sys.argv)
