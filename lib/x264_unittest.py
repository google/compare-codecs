#!/usr/bin/python
"""Unit tests for X.264 encoder module."""

import optimizer
import unittest
import test_tools
import x264

class TestX264(test_tools.FileUsingCodecTest):
  def test_Init(self):
    codec = x264.X264Codec()
    self.assertEqual(codec.name, 'x264')

  def test_OneBlackFrame(self):
    codec = x264.X264Codec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(50.0, my_optimizer.Score(encoding))


if __name__ == '__main__':
  unittest.main()


