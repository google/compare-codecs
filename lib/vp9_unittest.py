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
    self.assertTrue(0.03 < encoding.result['encode_cputime'] < 15.0)
    self.assertTrue(100 < encoding.result['bitrate'] < 500)
    self.assertTrue(500 < encoding.result['frame'][0]['size'] < 12000)

  def test_SpeedGroup(self):
    codec = vp9.Vp9Codec()
    self.assertEqual('5000', codec.SpeedGroup(5000))

if __name__ == '__main__':
  unittest.main()


