#!/usr/bin/python
"""Unit tests for mpeg1 fixed mode 1d encoder module."""

import encoder
import test_tools
import unittest

import vp8_mpeg_1d


class TestVp8Mpeg1dCodec(test_tools.FileUsingCodecTest):
  def test_Init(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    self.assertEqual('vp8-mp1', codec.name)

  def test_StartParams(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    params = codec.StartEncoder().parameters
    self.assertEqual(int(params.GetValue('key-q'))*2,
                     int(params.GetValue('fixed-q')))

  def test_ConfigFixups(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    fixups = codec.ConfigurationFixups(
      encoder.OptionValueSet(codec.option_set,
                             '--fixed-q=1 --gold-q=1 --key-q=3'))
    self.assertEqual('--fixed-q=6 --gold-q=4 --key-q=3', fixups.ToString())

  def test_SuggestTweakIncreasesCq(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    videofile = encoder.Videofile('foofile_640_480_30.yuv')
    my_encoder = codec.StartEncoder()
    encoding = encoder.Encoding(my_encoder, 500, videofile)
    encoding.result = { 'bitrate' : 1000 }
    # Since the bitrate is too high, the suggstion should be to increase it.
    new_encoding = codec.SuggestTweak(encoding)
    self.assertEqual('63', new_encoding.encoder.parameters.GetValue('key-q'))

  def test_SuggestTweakDecreasesCq(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    videofile = encoder.Videofile('foofile_640_480_30.yuv')
    my_encoder = codec.StartEncoder()
    encoding = encoder.Encoding(my_encoder, 500, videofile)
    encoding.result = { 'bitrate' : 200 }
    # Since the bitrate is too high, the suggstion should be to increase it.
    new_encoding = codec.SuggestTweak(encoding)
    self.assertEqual('0', new_encoding.encoder.parameters.GetValue('key-q'))

  def test_OneBlackFrame(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = codec.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(50.0, encoding.Score())


if __name__ == '__main__':
  unittest.main()

