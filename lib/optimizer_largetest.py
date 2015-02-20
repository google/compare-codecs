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

#
# Integration tests that are targeted at the optimizer.
# These are too large to be executed every iteration, but should be
# executed before every checkin.
#
import random
import re
import unittest

import encoder
import optimizer
import test_tools
import vp8


class DummyCodec(encoder.Codec):
  def __init__(self):
    super(DummyCodec, self).__init__('dummy')
    self.extension = 'fake'
    self.option_set = encoder.OptionSet(
      encoder.Option('score', ['0', '5', '10']),
      encoder.Option('another_parameter', ['yes']),
    )

  def StartEncoder(self, context):
    return encoder.Encoder(context,
                           encoder.OptionValueSet(self.option_set,
                                                  "--score=5"))

  def Execute(self, parameters, rate, videofile, workdir):
    # pylint: disable=W0613
    match = re.search(r'--score=(\d+)', parameters.ToString())
    if match:
      return {'psnr': int(match.group(1)), 'bitrate': 100}
    else:
      return {'psnr': -100, 'bitrate': 100}


class DummyVideofile(encoder.Videofile):
  def __init__(self, filename, clip_time):
    super(DummyVideofile, self).__init__(filename)
    self.clip_time = clip_time

  def ClipTime(self):
    return self.clip_time


def Returns1(target_bitrate, result):
  """Score function that returns a constant value."""
  # pylint: disable=W0613
  return 1.0

def ReturnsClipTime(target_bitrate, result):
  # pylint: disable=W0613
  return float(result['cliptime'])


class TestOptimization(test_tools.FileUsingCodecTest):
  # pylint: disable=R0201
  def test_OptimizeOverMultipleEncoders(self):
    """Run the optimizer for a few cycles with a real codec.

    This may turn out to be an over-heavy test for every-checkin testing."""
    my_fileset = test_tools.TestFileSet()
    my_codec = vp8.Vp8Codec()
    my_optimizer = optimizer.Optimizer(my_codec, my_fileset,
                                       cache_class=encoder.EncodingDiskCache)
    # Establish a baseline.
    for bitrate, videofile_name in my_fileset.AllFilesAndRates():
      videofile = encoder.Videofile(videofile_name)
      my_encoding = my_optimizer.BestEncoding(bitrate, videofile)
      my_encoding.Execute().Store()
    # Try to improve it.
    encoding_count = 0
    while encoding_count < 10:
      (bitrate, videofile_name) = random.choice(my_fileset.AllFilesAndRates())
      videofile = encoder.Videofile(videofile_name)
      next_encoding = my_optimizer.BestUntriedEncoding(bitrate, videofile)
      if not next_encoding:
        break
      encoding_count += 1
      next_encoding.Execute().Store()


if __name__ == '__main__':
  unittest.main()
