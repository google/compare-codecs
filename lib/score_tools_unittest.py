#!/usr/bin/python

import unittest

import score_tools

class TestScoreTools(unittest.TestCase):

  def test_DelayCalculation(self):
    # A list of frames of size 1000 bits.
    one_kilobit = [{'size':1000}, {'size':1000}]
    # At 30 kilobits per second, 30 frames per second, this should have
    # delay zero.
    self.assertAlmostEqual(0.0,
                      score_tools.DelayCalculation(one_kilobit, 30, 30000, 0.0))
    # At 15 kilobits per second, delay should be 1.0 - twice as much time
    # needed.
    self.assertAlmostEqual(1.0,
                      score_tools.DelayCalculation(one_kilobit, 30, 15000, 0.0))

if __name__ == '__main__':
  unittest.main()
