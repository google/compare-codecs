#!/usr/bin/python
"""Unit tests for Motion JPEG encoder module."""

import unittest
import test_tools

import mjpeg

class TestMotionJpegCodec(test_tools.FileUsingCodecTest):

  def test_OneBlackFrame(self):
    codec = mjpeg.MotionJpegCodec()
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    # Motion JPEG generates a massive file, so give it a large target bitrate.
    encoding = codec.BestEncoding(5000, videofile)
    encoding.Execute()
    self.assertLess(50.0, encoding.Score())

if __name__ == '__main__':
  unittest.main()


