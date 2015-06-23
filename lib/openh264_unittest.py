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
"""Unit tests for the openh264 encoder module."""

import optimizer
import unittest
import test_tools
import openh264


class TestOpenH264(test_tools.FileUsingCodecTest):
  def test_Init(self):
    codec = openh264.OpenH264Codec()
    self.assertEqual(codec.name, 'openh264')

  def test_OneBlackFrame(self):
    codec = openh264.OpenH264Codec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(40.0, my_optimizer.Score(encoding))

  def test_TenBlackFrames(self):
    codec = openh264.OpenH264Codec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithBlankFrames(
        'ten_black_frames_1024_768_30.yuv', 10)
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(40.0, my_optimizer.Score(encoding))

  def test_BitrateSensitivity(self):
    # Verify that bitrate varies at all when target bitrate
    # is changed. Hitting the bitrate is not tested.
    codec = openh264.OpenH264Codec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithNoisyFrames(
        'many_noisy_frames_1024_768_30.yuv', 10)
    encoding1 = my_optimizer.BestEncoding(1000, videofile)
    encoding1.Execute()
    encoding2 = my_optimizer.BestEncoding(10, videofile)
    encoding2.Execute()
    self.assertNotEquals(encoding1.result['bitrate'],
                         encoding2.result['bitrate'])

  def test_EncoderVersion(self):
    codec = openh264.OpenH264Codec()
    self.assertRegexpMatches(codec.EncoderVersion(),
                             r'openh264')


if __name__ == '__main__':
  unittest.main()
