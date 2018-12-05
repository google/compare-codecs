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
"""Unit tests for HEVC JM encoder module."""

import optimizer
import unittest
import test_tools
import hevc_jm


class TestHevc(test_tools.FileUsingCodecTest):
  def test_Init(self):
    codec = hevc_jm.HevcCodec()
    self.assertEqual(codec.name, 'hevc')

  def test_OneBlackFrame(self):
    codec = hevc_jm.HevcCodec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(40.0, my_optimizer.Score(encoding))

  def test_MoreBlackFrames(self):
    codec = hevc_jm.HevcCodec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithBlankFrames(
        'more_black_frames_1024_768_30.yuv', 8)
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(40.0, my_optimizer.Score(encoding))

  def test_EncoderVersion(self):
    codec = hevc_jm.HevcCodec()
    self.assertRegexpMatches(codec.EncoderVersion(),
                             r'HM software')


if __name__ == '__main__':
  unittest.main()
