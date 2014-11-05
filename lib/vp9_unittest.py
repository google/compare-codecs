#!/usr/bin/python
"""Unit tests for encoder module."""

import unittest
import test_tools

import vp9

class TestVp9(test_tools.FileUsingCodecTest):

  def test_Init(self):
    codec = vp9.Vp9Codec()
    self.assertEqual(codec.name, 'vp9')

  def test_OneBlackFrame(self):
    codec = vp9.Vp9Codec()
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = codec.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(50.0, encoding.Score())
    self.assertEqual(1, len(encoding.result['frame']))
    # Check that expected results are present and "reasonable".
    print encoding.result
    self.assertTrue(0.05 < encoding.result['encode_cputime'] < 15.0)
    self.assertTrue(100 < encoding.result['bitrate'] < 500)
    self.assertTrue(500 < encoding.result['frame'][0]['size'] < 12000)

  def test_SpeedGroup(self):
    codec = vp9.Vp9Codec()
    self.assertEqual('5000', codec.SpeedGroup(5000))

if __name__ == '__main__':
  unittest.main()


