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
"""Unit tests for Motion JPEG encoder module."""

import optimizer
import unittest
import test_tools

import mjpeg

class TestMotionJpegCodec(test_tools.FileUsingCodecTest):

  def test_OneBlackFrame(self):
    codec = mjpeg.MotionJpegCodec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    # Motion JPEG generates a massive file, so give it a large target bitrate.
    encoding = my_optimizer.BestEncoding(5000, videofile)
    encoding.Execute()
    self.assertLess(50.0, my_optimizer.Score(encoding))

if __name__ == '__main__':
  unittest.main()

