#!/usr/bin/python
"""Unit tests for encoder module."""

import unittest
import encoder

import vp8_cq

class TestVp8Cq(unittest.TestCase):
  def test_Init(self):
    codec = vp8_cq.Vp8CodecCqMode()
    self.assertEqual('vp8-cq', codec.name)
    # Verifying that the default config's value for min-q is still 32.
    # This is required for later tests to work properly.
    self.assertEqual('32',
                     codec.StartEncoder().parameters.GetValue('min-q'))

  def test_Fixup(self):
    codec = vp8_cq.Vp8CodecCqMode()
    config = encoder.OptionValueSet(codec.option_set, '--min-q=47 --max-q=33')
    self.assertEqual(codec.ConfigurationFixups(config),
                     '--min-q=47 --max-q=47')

  def test_SuggestTweakIncreasesCq(self):
    codec = vp8_cq.Vp8CodecCqMode()
    videofile = encoder.Videofile('foofile_640_480_30.yuv')
    my_encoder = codec.StartEncoder()
    encoding = encoder.Encoding(my_encoder, 500, videofile)
    encoding.result = { 'bitrate' : 1000 }
    # Since the bitrate is too high, the suggstion should be to increase it.
    new_encoding = codec.SuggestTweak(encoding)
    self.assertEqual('33', new_encoding.encoder.parameters.GetValue('min-q'))

  def test_SuggestTweakDecreasesCq(self):
    codec = vp8_cq.Vp8CodecCqMode()
    videofile = encoder.Videofile('foofile_640_480_30.yuv')
    my_encoder = codec.StartEncoder()
    encoding = encoder.Encoding(my_encoder, 500, videofile)
    encoding.result = { 'bitrate' : 200 }
    # Since the bitrate is too high, the suggstion should be to increase it.
    new_encoding = codec.SuggestTweak(encoding)
    self.assertEqual('31', new_encoding.encoder.parameters.GetValue('min-q'))

if __name__ == '__main__':
  unittest.main()
