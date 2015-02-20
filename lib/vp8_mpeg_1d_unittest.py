#!/usr/bin/python
# Copyright 2014 Google.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for mpeg1 fixed mode 1d encoder module."""

import encoder
import optimizer
import test_tools
import unittest

import vp8_mpeg_1d


class TestVp8Mpeg1dCodec(test_tools.FileUsingCodecTest):
  def test_Init(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    self.assertEqual('vp8-mp1', codec.name)

  def test_StartParams(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    my_optimizer = optimizer.Optimizer(codec)
    params = codec.StartEncoder(my_optimizer.context).parameters
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
    my_optimizer = optimizer.Optimizer(codec)
    my_encoder = codec.StartEncoder(my_optimizer.context)
    encoding = encoder.Encoding(my_encoder, 500, videofile)
    encoding.result = {'bitrate': 1000}
    # Since the bitrate is too high, the suggstion should be to increase it.
    new_encoding = codec.SuggestTweak(encoding)
    self.assertEqual('63', new_encoding.encoder.parameters.GetValue('key-q'))

  def test_SuggestTweakDecreasesCq(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    videofile = encoder.Videofile('foofile_640_480_30.yuv')
    my_optimizer = optimizer.Optimizer(codec)
    my_encoder = codec.StartEncoder(my_optimizer.context)
    encoding = encoder.Encoding(my_encoder, 500, videofile)
    encoding.result = {'bitrate': 200}
    # Since the bitrate is too high, the suggstion should be to increase it.
    new_encoding = codec.SuggestTweak(encoding)
    self.assertEqual('0', new_encoding.encoder.parameters.GetValue('key-q'))

  def test_OneBlackFrame(self):
    codec = vp8_mpeg_1d.Vp8CodecMpeg1dMode()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(50.0, my_optimizer.Score(encoding))


if __name__ == '__main__':
  unittest.main()

