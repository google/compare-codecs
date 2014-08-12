#!/usr/bin/python
#
# Unit tests for the visual_metrics package.
#
import unittest

import visual_metrics

def LinearVector(slope=0.0, offset=0.0):
  """A point pair set that has points in a straight line."""
  return [[float(i), float(i*slope)+offset] for i in (10, 20, 30, 40)]

class TestVisualMetricsFunctions(unittest.TestCase):

  def test_GraphBetter(self):
    metric_set_1 = LinearVector(slope=1)
    # A set compared to itself should have zero difference.
    self.assertEquals(0.0, visual_metrics.GraphBetter(metric_set_1, metric_set_1, use_set2_as_base=False))
    # A test set at exactly double the bitrate. Still linear.
    metric_set_2 = LinearVector(slope=2)
    self.assertAlmostEqual(50.0, 100*visual_metrics.GraphBetter(metric_set_1, metric_set_2, use_set2_as_base=False))
    self.assertAlmostEqual(-100.0, 100*visual_metrics.GraphBetter(metric_set_2, metric_set_1, use_set2_as_base=False))
    self.assertAlmostEqual(100.0, 100*visual_metrics.GraphBetter(metric_set_1, metric_set_2, use_set2_as_base=True))
    self.assertAlmostEqual(-50.0, 100*visual_metrics.GraphBetter(metric_set_2, metric_set_1, use_set2_as_base=True))

  def test_bdsnr(self):
    metric_set_1 = LinearVector(slope=1)
    self.assertEquals(0.0, visual_metrics.bdsnr(metric_set_1, metric_set_1))
    # A test set at exactly double the bitrate. Still linear.
    # This test depends on the length of the vector, so not a good fit for bdsnr.
    metric_set_2 = LinearVector(slope=2)
    self.assertAlmostEqual(21.6, visual_metrics.bdsnr(metric_set_1, metric_set_2), delta=0.5)
    self.assertAlmostEqual(-21.6, visual_metrics.bdsnr(metric_set_2, metric_set_1), delta=0.5)
    # A test with a constant improvement in metric.
    metric_set_3 = LinearVector(slope=1, offset=2)
    self.assertAlmostEqual(2.0, visual_metrics.bdsnr(metric_set_1, metric_set_3))
    self.assertAlmostEqual(-2.0, visual_metrics.bdsnr(metric_set_3, metric_set_1))

  def test_bdrate(self):
    metric_set_1 = LinearVector(slope=1)
    self.assertEquals(0.0, visual_metrics.bdrate(metric_set_1, metric_set_1))
    # A test set at exactly double the bitrate. Still linear.
    metric_set_2 = LinearVector(slope=2)
    self.assertAlmostEqual(-50.0, visual_metrics.bdrate(metric_set_1, metric_set_2), delta=0.5)
    self.assertAlmostEqual(100.0, visual_metrics.bdrate(metric_set_2, metric_set_1), delta=2.0)

  def test_DataSetBetter(self):
    metric_set_1 = LinearVector(slope=1)
    metric_set_2 = LinearVector(slope=2)
    metric_set_3 = LinearVector(slope=1, offset=2)
    self.assertAlmostEqual(100.0, visual_metrics.DataSetBetter(metric_set_1, metric_set_2, 'avg'))
    self.assertAlmostEqual(100.0, visual_metrics.DataSetBetter(metric_set_1, metric_set_2, 'bdrate'),
                           delta=2.0)
    self.assertAlmostEqual(2.0, visual_metrics.DataSetBetter(metric_set_1, metric_set_3, 'dsnr'))

  def test_HtmlPage(self):
    page_template = 'Test: //%%filestable_dpsnr%%//'
    expected_result = 'Test: result'
    filestable = {'dsnr': 'result', 'avg': 'notused', 'drate': 'notused'}
    result = visual_metrics.HtmlPage(page_template, filestable, None, None)
    self.assertEquals(expected_result, result)

if __name__ == '__main__':
    unittest.main()
