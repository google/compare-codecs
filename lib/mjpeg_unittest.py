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

import encoder
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

  def test_ParametersSet(self):
    codec = mjpeg.MotionJpegCodec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    my_encoder = encoder.Encoder(my_optimizer.context,
        encoder.OptionValueSet(codec.option_set, '-qmin 1 -qmax 2',
                               formatter=codec.option_formatter))
    encoding = my_encoder.Encoding(5000, videofile)
    encoding.Execute()
    self.assertLess(50.0, my_optimizer.Score(encoding))

  def test_ParametersAdjusted(self):
    codec = mjpeg.MotionJpegCodec()
    my_optimizer = optimizer.Optimizer(codec)
    my_encoder = encoder.Encoder(my_optimizer.context,
        encoder.OptionValueSet(codec.option_set, '-qmin 1 -qmax 1',
                               formatter=codec.option_formatter))
    self.assertEquals('1', my_encoder.parameters.GetValue('qmin'))
    self.assertEquals('1', my_encoder.parameters.GetValue('qmax'))
    # qmax is less than qmin. Should be adjusted to be above.
    my_encoder = encoder.Encoder(my_optimizer.context,
        encoder.OptionValueSet(codec.option_set, '-qmin 2 -qmax 1',
                               formatter=codec.option_formatter))
    self.assertEquals('2', my_encoder.parameters.GetValue('qmin'))
    self.assertEquals('2', my_encoder.parameters.GetValue('qmax'))
    # qmin is not given, qmax set below default for qmin.
    my_encoder = encoder.Encoder(my_optimizer.context,
        encoder.OptionValueSet(codec.option_set, '-qmax 0',
                               formatter=codec.option_formatter))
    self.assertEquals('1', my_encoder.parameters.GetValue('qmax'))


if __name__ == '__main__':
  unittest.main()
