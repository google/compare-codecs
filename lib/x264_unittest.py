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
"""Unit tests for X.264 encoder module."""

import encoder
import optimizer
import unittest
import test_tools
import x264

class TestX264(test_tools.FileUsingCodecTest):
  def test_Init(self):
    codec = x264.X264Codec()
    self.assertEqual(codec.name, 'x264')

  def test_OneBlackFrame(self):
    codec = x264.X264Codec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(40.0, my_optimizer.Score(encoding))

  def test_TenBlackFrames(self):
    codec = x264.X264Codec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithBlankFrames(
        'ten_black_frames_1024_768_30.yuv', 10)
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(40.0, my_optimizer.Score(encoding))

  def test_VbvMaxrateFlag(self):
    codec = x264.X264Codec()
    context = encoder.Context(codec)
    my_encoder = codec.StartEncoder(context)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    encoding = my_encoder.Encoding(1000, videofile)
    # The start encoder should have no bitrate.
    commandline = encoding.EncodeCommandLine()
    self.assertNotRegexpMatches(commandline, 'vbv-maxrate')
    # Add in the use-vbv-maxrate parameter.
    new_encoder = encoder.Encoder(context,
        my_encoder.parameters.ChangeValue('use-vbv-maxrate', 'use-vbv-maxrate'))
    encoding = new_encoder.Encoding(1000, videofile)
    commandline = encoding.EncodeCommandLine()
    # vbv-maxrate should occur, but not use-vbv-maxrate.
    self.assertRegexpMatches(commandline, '--vbv-maxrate 1000 ')
    self.assertNotRegexpMatches(commandline, 'use-vbv-maxrate')

  def test_Threading(self):
    codec = x264.X264Codec()
    context = encoder.Context(codec, encoder.EncodingDiskCache)
    one_thread_encoder = codec.StartEncoder(context).ChangeValue('threads', 1)
    two_thread_encoder = codec.StartEncoder(context).ChangeValue('threads', 2)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    one_encoding = one_thread_encoder.Encoding(1000, videofile)
    one_encoding.Execute()
    two_encoding = two_thread_encoder.Encoding(1000, videofile)
    two_encoding.Execute()
    self.assertAlmostEquals(float(one_encoding.Result()['psnr']),
                            float(two_encoding.Result()['psnr']))

  def test_EncoderVersion(self):
    codec = x264.X264Codec()
    self.assertRegexpMatches(codec.EncoderVersion(), r'x264 \d')


if __name__ == '__main__':
  unittest.main()
