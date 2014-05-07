#!/usr/bin/python
"""Unit tests for encoder module."""

import unittest
import encoder

import vp8

class TestVp8(unittest.TestCase):
  def test_Init(self):
    codec = vp8.Vp8Codec()
    self.assertEqual(codec.name, 'vp8')

  def test_ScoreResult(self):
    codec = vp8.Vp8Codec()
    result = {'bitrate': 100, 'psnr': 10.0}
    self.assertEqual(10.0, codec.ScoreResult(100, result))
    self.assertEqual(10.0, codec.ScoreResult(1000, result))
    # Score is reduced by 0.1 per kbps overrun.
    self.assertAlmostEqual(10.0 - 0.1, codec.ScoreResult(99, result))
    # Score floors at 0.1 for very large overruns.
    self.assertAlmostEqual(0.1, codec.ScoreResult(1, result))
    self.assertFalse(codec.ScoreResult(100, None))

if __name__ == '__main__':
    unittest.main()


