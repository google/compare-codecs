#!/usr/bin/python
"""Unit tests for mpeg1 fixed mode 1d encoder module."""

import unittest
import encoder

import vp8_mpeg_1d


class TestVp8Mpeg1dCodec(unittest.TestCase):
  def test_Init(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    self.assertEqual('vp8-mp1', codec.name)

  def test_StartParams(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    params = codec.start_encoder.parameters
    self.assertEqual(int(encoder.Option('key-q').GetValue(params))*2,
                     int(encoder.Option('fixed-q').GetValue(params)))

  def test_ConfigFixups(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    fixups = codec.ConfigurationFixups('--fixed-q=1 --gold-q=1 --key-q=3')
    self.assertEqual('--fixed-q=6 --gold-q=4 --key-q=3', fixups)

if __name__ == '__main__':
    unittest.main()

