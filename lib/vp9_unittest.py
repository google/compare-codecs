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
"""Unit tests for encoder module."""

import encoder
import optimizer
import unittest
import test_tools

import vp9

class TestVp9(test_tools.FileUsingCodecTest):

  def test_Init(self):
    codec = vp9.Vp9Codec()
    self.assertEqual(codec.name, 'vp9')

  def test_OneBlackFrame(self):
    codec = vp9.Vp9Codec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(50.0, my_optimizer.Score(encoding))
    self.assertEqual(1, len(encoding.result['frame']))
    # Check that expected results are present and "reasonable".
    print encoding.result
    self.assertTrue(0.02 < encoding.result['encode_cputime'] < 15.0)
    self.assertTrue(100 < encoding.result['bitrate'] < 500)
    self.assertTrue(500 < encoding.result['frame'][0]['size'] < 12000)

  def test_SpeedGroup(self):
    codec = vp9.Vp9Codec()
    self.assertEqual('5000', codec.SpeedGroup(5000))

  def test_Passes(self):
    """This test checks that both 1-pass and 2-pass encoding works."""
    codec = vp9.Vp9Codec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    start_encoder = codec.StartEncoder(my_optimizer.context)
    encoder1 = encoder.Encoder(my_optimizer.context,
        start_encoder.parameters.ChangeValue('passes', 1))
    encoding1 = encoder1.Encoding(1000, videofile)
    encoder2 = encoder.Encoder(my_optimizer.context,
        start_encoder.parameters.ChangeValue('passes', 2))
    encoding2 = encoder2.Encoding(1000, videofile)
    encoding1.Execute()
    encoding2.Execute()
    self.assertTrue(encoding1.result)
    self.assertTrue(encoding2.result)


if __name__ == '__main__':
  unittest.main()
