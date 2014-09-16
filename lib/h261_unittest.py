#!/usr/bin/python
"""Unit tests for VP8 MPEG mode encoder module."""

import encoder
import unittest
import test_tools

import h261

class TestH261Codec(test_tools.FileUsingCodecTest):

  def test_OneBlackFrame(self):
    codec = h261.H261Codec()
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = codec.BestEncoding(1000, videofile)
    encoding.Execute()
    # H.261 does badly at generating a black frame. Bug?
    self.assertLess(48.0, encoding.Score())

if __name__ == '__main__':
  unittest.main()


