#!/usr/bin/python
"""Unit tests for H.261 encoder module."""
import optimizer
import unittest
import test_tools

import h261

class TestH261Codec(test_tools.FileUsingCodecTest):

  def test_OneBlackFrame(self):
    codec = h261.H261Codec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # H.261 does badly at generating a black frame. Bug?
    self.assertLess(48.0, my_optimizer.Score(encoding))

if __name__ == '__main__':
  unittest.main()


