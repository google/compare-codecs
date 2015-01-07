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

  def test_ScorePsnrBitrate(self):
    result = {'bitrate': 100, 'psnr': 10.0}
    self.assertEqual(10.0, score_tools.ScorePsnrBitrate(100, result))
    self.assertEqual(10.0, score_tools.ScorePsnrBitrate(1000, result))
    # Score is reduced by 0.1 per kbps overrun.
    self.assertAlmostEqual(10.0 - 0.1, score_tools.ScorePsnrBitrate(99, result))
    # Score floors at 0.1 for very large overruns.
    self.assertAlmostEqual(0.1, score_tools.ScorePsnrBitrate(1, result))
    self.assertFalse(score_tools.ScorePsnrBitrate(100, None))

  def test_ScoreCpuPsnr(self):
    result = {'bitrate': 100, 'psnr': 10.0, 'cliptime': 1.0,
              'encode_cputime': 0.7}
    self.assertEqual(10.0, score_tools.ScoreCpuPsnr(100, result))
    # Test 1.01 percent overrun in bitrate.
    self.assertAlmostEqual(10.0 - 10 * (100.0 / 99 - 1),
                           score_tools.ScoreCpuPsnr(99, result))
    result['encode_cputime'] = 1.1
    self.assertAlmostEqual(0.0, score_tools.ScoreCpuPsnr(100, result))

  def test_PickScorer(self):
    self.assertEqual(score_tools.ScoreCpuPsnr, score_tools.PickScorer('rt'))
    with self.assertRaises(KeyError):
      score_tools.PickScorer('unknown')

if __name__ == '__main__':
  unittest.main()
