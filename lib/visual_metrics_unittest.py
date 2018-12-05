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
# Unit tests for the visual_metrics package.
#
import encoder
import unittest

import visual_metrics

def LinearVector(slope=0.0, offset=0.0):
  """A point pair set that has points in a straight line."""
  return [[float(i), float(i*slope)+offset] for i in (10, 20, 30, 40)]


class FakeCodec(object):
  def __init__(self):
    self.name = 'mock'
    self.option_set = encoder.OptionSet()


class FakeContext(object):
  def __init__(self):
    self.codec = FakeCodec()


class FakeOptimizer(object):
  def __init__(self):
    self.context = FakeContext()

  def BestEncoding(self, rate, videofile):
    # pylint: disable=W0613,R0201
    return FakeEncoding()

  def Score(self, encoding):
    # pylint: disable=R0201, W0613
    return 1.0


class FakeEncoder(object):
  def Hashname(self):
    # pylint: disable=no-self-use
    return 'FakeName'


class FakeEncoding(object):
  def __init__(self):
    self.result = {'bitrate': 1000, 'psnr': 1.0}
    self.encoder = FakeEncoder()
    self.bitrate = 1000

  def Execute(self):
    pass

  def Store(self):
    pass

  def Result(self):
    return self.result

  def ResultWithoutFrameData(self):
    return self.Result()

  def EncodeCommandLine(self):
    # pylint: disable=no-self-use
    return '# Fake command line'


class TestVisualMetricsFunctions(unittest.TestCase):

  def test_GraphBetter(self):
    metric_set_1 = LinearVector(slope=1)
    # A set compared to itself should have zero difference.
    self.assertEquals(0.0,
                      visual_metrics.GraphBetter(metric_set_1, metric_set_1,
                                                 use_set2_as_base=False))
    # A test set at exactly double the bitrate. Still linear.
    metric_set_2 = LinearVector(slope=2)
    self.assertAlmostEqual(
      50.0,
      100*visual_metrics.GraphBetter(metric_set_1,
                                     metric_set_2,
                                     use_set2_as_base=False))
    self.assertAlmostEqual(
      -100.0, 100*visual_metrics.GraphBetter(metric_set_2, metric_set_1,
                                             use_set2_as_base=False))
    self.assertAlmostEqual(
      100.0, 100*visual_metrics.GraphBetter(metric_set_1, metric_set_2,
                                            use_set2_as_base=True))
    self.assertAlmostEqual(
      -50.0, 100*visual_metrics.GraphBetter(metric_set_2, metric_set_1,
                                            use_set2_as_base=True))

  def test_bdsnr(self):
    metric_set_1 = LinearVector(slope=1)
    self.assertEquals(0.0, visual_metrics.bdsnr(metric_set_1, metric_set_1))
    # A test set at exactly double the bitrate. Still linear.
    # This test depends on the length of the vector, so not a good fit for
    # bdsnr.
    metric_set_2 = LinearVector(slope=2)
    self.assertAlmostEqual(
      21.6, visual_metrics.bdsnr(metric_set_1, metric_set_2), delta=0.5)
    self.assertAlmostEqual(
      -21.6, visual_metrics.bdsnr(metric_set_2, metric_set_1), delta=0.5)
    # A test with a constant improvement in metric.
    metric_set_3 = LinearVector(slope=1, offset=2)
    self.assertAlmostEqual(
      2.0, visual_metrics.bdsnr(metric_set_1, metric_set_3))
    self.assertAlmostEqual(
      -2.0, visual_metrics.bdsnr(metric_set_3, metric_set_1))

  def test_bdrate(self):
    metric_set_1 = LinearVector(slope=1)
    self.assertEquals(0.0, visual_metrics.bdrate(metric_set_1, metric_set_1))
    # A test set at exactly double the bitrate. Still linear.
    metric_set_2 = LinearVector(slope=2)
    self.assertAlmostEqual(
      -50.0, visual_metrics.bdrate(metric_set_1, metric_set_2), delta=0.5)
    self.assertAlmostEqual(
      100.0, visual_metrics.bdrate(metric_set_2, metric_set_1), delta=2.0)

  def test_DataSetBetter(self):
    metric_set_1 = LinearVector(slope=1)
    metric_set_2 = LinearVector(slope=2)
    metric_set_3 = LinearVector(slope=1, offset=2)
    self.assertAlmostEqual(
      100.0, visual_metrics.DataSetBetter(metric_set_1, metric_set_2, 'avg'))
    self.assertAlmostEqual(
      100.0, visual_metrics.DataSetBetter(metric_set_1, metric_set_2, 'bdrate'),
                           delta=2.0)
    self.assertAlmostEqual(
      2.0, visual_metrics.DataSetBetter(metric_set_1, metric_set_3, 'dsnr'))

  def test_HtmlPage(self):
    page_template = 'Test: //%%filestable_dpsnr%%//'
    expected_result = 'Test: result'
    filestable = {'dsnr': 'result', 'avg': 'notused', 'drate': 'notused'}
    result = visual_metrics.HtmlPage(page_template,
                                     filestable=filestable)
    self.assertEquals(expected_result, result)

  def test_ListOneTarget(self):
    datatable = {}
    filename = 'file_10x10_10'
    videofile = encoder.Videofile(filename)
    visual_metrics.ListOneTarget([FakeOptimizer()], 1000, videofile,
                                 False, datatable)
    self.assertEquals(1, len(datatable['mock'][filename]))

  def test_BuildComparisonTable(self):
    datatable = {
      'codec1': {'dummyfile': [
        {'result': {'bitrate': 100, 'psnr': 30.0}},
        {'result': {'bitrate': 200, 'psnr': 40.0}}
      ]},
      'codec2': {'dummyfile': [
        {'result': {'bitrate': 100, 'psnr': 31.0}},
        {'result': {'bitrate': 200, 'psnr': 42.0}}
      ]},
    }
    result = visual_metrics.BuildComparisonTable(datatable, 'avg',
                                                 'codec1', ['codec2'])
    self.assertEquals(2, len(result))
    self.assertEquals('OVERALL avg', result[1]['file'])
    self.assertIn('codec2', result[0])

  def test_BuildComparisonTableSkipsNan(self):
    datatable = {
      # This generates a NaN, because the two slopes are opposite.
      # The correct response is to not report on the result.
      'codec1': {'dummyfile': [
        {'result': {'bitrate': 100, 'psnr': 30.0}},
        {'result': {'bitrate': 200, 'psnr': 40.0}}
      ]},
      'codec2': {'dummyfile': [
        {'result': {'bitrate': 300, 'psnr': 50.0}},
        {'result': {'bitrate': 400, 'psnr': 40.0}}
      ]},
    }
    result = visual_metrics.BuildComparisonTable(datatable, 'drate',
                                                 'codec1', ['codec2'])
    self.assertEquals(2, len(result))
    self.assertNotIn('codec2', result[0])

  def test_CrossPerformanceGvizTableWithoutData(self):
    datatable = {'dummy1':{}}
    metric = 'meaningless'
    codecs = ['dummy1', 'dummy2']
    # This should result in an empty table, with correct headers and col1.
    data_table = visual_metrics.CrossPerformanceGvizTable(
        datatable, metric, codecs, 'psnr')
    self.assertEquals(2, data_table.NumberOfRows())

  def test_CrossPerformanceGvizTableWithData(self):
    datatable = {
      'codec1': {'dummyfile': [
        {'result': {'bitrate': 100, 'psnr': 30.0}},
        {'result': {'bitrate': 200, 'psnr': 40.0}}
      ]},
      'codec2': {'dummyfile' : [
        {'result': {'bitrate': 100, 'psnr': 31.0}},
        {'result': {'bitrate': 200, 'psnr': 42.0}}
      ]},
    }
    result = visual_metrics.CrossPerformanceGvizTable(datatable, 'avg',
                                                      ['codec1', 'codec2'],
                                                      'rt')
    self.assertEquals(3, len(result.columns))
    self.assertEquals(2, result.NumberOfRows())


if __name__ == '__main__':
  unittest.main()
