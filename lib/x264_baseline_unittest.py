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
import x264_baseline

class TestX264Baseline(test_tools.FileUsingCodecTest):
  def test_Init(self):
    codec = x264_baseline.X264BaselineCodec()
    self.assertEqual(codec.name, 'x264-base')

  def test_OneBlackFrame(self):
    codec = x264_baseline.X264BaselineCodec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Most codecs should be good at this.
    self.assertLess(40.0, my_optimizer.Score(encoding))

  def test_HasBaselineFlag(self):
    codec = x264_baseline.X264BaselineCodec()
    context = encoder.Context(codec)
    my_encoder = codec.StartEncoder(context)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    encoding = my_encoder.Encoding(1000, videofile)
    commandline = encoding.EncodeCommandLine()
    self.assertRegexpMatches(commandline, '--profile baseline ')

if __name__ == '__main__':
  unittest.main()


