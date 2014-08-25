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
    params = codec.StartEncoder().parameters
    self.assertEqual(int(params.GetValue('key-q'))*2,
                     int(params.GetValue('fixed-q')))

  def test_ConfigFixups(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    fixups = codec.ConfigurationFixups(
      encoder.OptionValueSet(codec.option_set, '--fixed-q=1 --gold-q=1 --key-q=3'))
    self.assertEqual('--fixed-q=6 --gold-q=4 --key-q=3', fixups.ToString())

if __name__ == '__main__':
    unittest.main()

