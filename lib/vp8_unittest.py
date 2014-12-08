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

import optimizer
import test_tools
import unittest

import vp8

class TestVp8(test_tools.FileUsingCodecTest):

  def test_Init(self):
    codec = vp8.Vp8Codec()
    self.assertEqual(codec.name, 'vp8')

  def test_OneBlackFrame(self):
    codec = vp8.Vp8Codec()
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
    self.assertTrue(0.01 < encoding.result['encode_cputime'] < 0.5)
    self.assertTrue(400 < encoding.result['bitrate'] < 500)
    self.assertTrue(10000 < encoding.result['frame'][0]['size'] < 12000)

  def test_SpeedGroup(self):
    codec = vp8.Vp8Codec()
    self.assertEqual('5000', codec.SpeedGroup(5000))

if __name__ == '__main__':
  unittest.main()


