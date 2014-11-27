#!/usr/bin/python
"""Unit tests for VP8 MPEG mode encoder module."""

import encoder
import optimizer
import unittest
import test_tools

import vp8_mpeg

class TestVp8Mpeg(test_tools.FileUsingCodecTest):

  def test_OneBlackFrame(self):
    codec = vp8_mpeg.Vp8CodecMpegMode()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(50.0, my_optimizer.Score(encoding))

  def test_ConfigurationFixups(self):
    codec = vp8_mpeg.Vp8CodecMpegMode()
    fixups = codec.ConfigurationFixups(
      encoder.OptionValueSet(codec.option_set,
                             '--fixed-q=6 --gold-q=27 --key-q=8'))
    self.assertEqual('--fixed-q=6 --gold-q=6 --key-q=6', fixups.ToString())


if __name__ == '__main__':
  unittest.main()


