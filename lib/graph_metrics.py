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
#

"""Functions for computing graph-based metrics over scores."""

import encoder
import fileset_picker
import math
import numpy
import optimizer

class Error(Exception):
  pass

class ScoreGroup(object):
  """The scores describing a single codec's run results."""

  def __init__(self, filename, codec, score_function):
    self.name = codec.name
    self.videofile = encoder.Videofile(filename)
    self.fileset = optimizer.FileAndRateSet()
    self.fileset.AddFilesAndRates([filename],
        fileset_picker.ChooseRates(self.videofile.width,
                                   self.videofile.framerate))
    self.my_optimizer = optimizer.Optimizer(codec,
                                            file_set=self.fileset,
                                            score_function=score_function)
    self.filename = filename
    self.encoder = self.my_optimizer.BestOverallEncoder()
    if not self.encoder:
      raise Error('No overall encoder for %s on %s' % (codec.name, filename))
    self.points = None

  def dataPoints(self):
    if not self.points:
      self.points = []
      for rate in self.fileset.AllRatesForFile(self.filename):
        encoding = self.encoder.Encoding(rate, self.videofile)
        encoding.Recover()
        self.points.append([encoding.Result()['bitrate'],
                            encoding.Result()['psnr']])
    return self.points

def BdRate(group1, group2):
  """Compute the BD-rate between two score groups.

  The returned object also contains the range of PSNR values used
  to compute the result.

  Bjontegaard's metric allows to compute the average % saving in bitrate
  between two rate-distortion curves [1].

  rate1,psnr1 - RD points for curve 1
  rate2,psnr2 - RD points for curve 2

  adapted from code from: (c) 2010 Giuseppe Valenzise
  copied from code by jzern@google.com, jimbankoski@google.com

  """
  # pylint: disable=too-many-locals
  metric_set1 = group1.dataPoints()
  metric_set2 = group2.dataPoints()

  # numpy plays games with its exported functions.
  # pylint: disable=no-member
  # pylint: disable=too-many-locals
  # pylint: disable=bad-builtin
  psnr1 = [x[1] for x in metric_set1]
  psnr2 = [x[1] for x in metric_set2]

  log_rate1 = map(math.log, [x[0] for x in metric_set1])
  log_rate2 = map(math.log, [x[0] for x in metric_set2])

  # Best cubic poly fit for graph represented by log_ratex, psrn_x.
  poly1 = numpy.polyfit(psnr1, log_rate1, 3)
  poly2 = numpy.polyfit(psnr2, log_rate2, 3)

  # Integration interval.
  min_int = max([min(psnr1), min(psnr2)])
  max_int = min([max(psnr1), max(psnr2)])

  # find integral
  p_int1 = numpy.polyint(poly1)
  p_int2 = numpy.polyint(poly2)

  # Calculate the integrated value over the interval we care about.
  int1 = numpy.polyval(p_int1, max_int) - numpy.polyval(p_int1, min_int)
  int2 = numpy.polyval(p_int2, max_int) - numpy.polyval(p_int2, min_int)

  # Calculate the average improvement.
  avg_exp_diff = (int2 - int1) / (max_int - min_int)

  # In really bad formed data the exponent can grow too large.
  # clamp it.
  if avg_exp_diff > 200:
    avg_exp_diff = 200

  # Convert to a percentage.
  avg_diff = (math.exp(avg_exp_diff) - 1) * 100

  return {'difference': avg_diff, 'psnr':[min_int, max_int]}

class AnalysisResult(object):
  """The result of a graph analysis of a single file.

  This is able to provide a numeric difference in rates,
  as well as a longer text description of the result."""

  def __init__(self, filename, codecs, score_function):
    self.input_data = []
    for codec in codecs:
      self.input_data.append(ScoreGroup(filename, codec, score_function))
    self.scores = []

  def score(self):
    return self.scores

  def run(self):
    self.scores = [(x.name, BdRate(self.input_data[0], x))
                   for x in self.input_data[1:]]

  def analysis(self):
    return ('No analysis performed\n' +
            'Base codec is ' + self.input_data[0].name)


def BdRateAnalysis(filename, codecs, score_function):
  result = AnalysisResult(filename, codecs, score_function)
  result.run()
  return result
