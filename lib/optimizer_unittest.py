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
# Unit tests for the optimizer.
#
import re
import unittest

import encoder
import optimizer

class DummyCodec(encoder.Codec):
  def __init__(self):
    super(DummyCodec, self).__init__('dummy')
    self.extension = 'fake'
    self.option_set = encoder.OptionSet(
      encoder.Option('score',  ['0', '5', '10']),
    )

  def StartEncoder(self, context):
    return encoder.Encoder(context,
                           encoder.OptionValueSet(self.option_set,
                                                  "--score=5"))

  def Execute(self, parameters, rate, videofile, workdir):
    # pylint: disable=W0613
    m = re.search(r'--score=(\d+)', parameters.ToString())
    if m:
      return {'psnr': int(m.group(1)), 'bitrate': 100}
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


class TestOptimizer(unittest.TestCase):
  def setUp(self):
    self.codec = DummyCodec()
    self.file_set = None
    self.cache_class = encoder.EncodingMemoryCache
    self.score_function = None
    self.videofile = DummyVideofile('foofile_640_480_30.yuv', clip_time=1)

  def StdOptimizer(self):
    return optimizer.Optimizer(self.codec, self.file_set,
                               cache_class=self.cache_class)

  def testInit(self):
    optimizer.Optimizer(self.codec, self.file_set,
                        cache_class=self.cache_class)

  def test_AlternateScorer(self):
    my_optimizer = optimizer.Optimizer(self.codec, self.file_set,
                                       cache_class=self.cache_class,
                                       score_function=Returns1)
    my_optimizer.BestEncoding(100, self.videofile).Execute().Store()
    self.assertEqual(1,
        my_optimizer.Score(my_optimizer.BestEncoding(100, self.videofile)))

  def test_FirstBestEncodingNoScore(self):
    my_optimizer = self.StdOptimizer()
    encoding = my_optimizer.BestEncoding(100, self.videofile)
    self.assertIsNone(encoding.Result())

  def test_BestEncodingOneAlternative(self):
    my_optimizer = self.StdOptimizer()
    my_optimizer.BestEncoding(100, self.videofile).Store()
    encoding = my_optimizer.BestEncoding(100, self.videofile)
    self.assertEqual(encoding.videofile, self.videofile)

  def test_BestEncodingExecuteGivesScore(self):
    my_optimizer = self.StdOptimizer()
    my_optimizer.BestEncoding(100, self.videofile).Execute().Store()
    self.assertEqual(5, my_optimizer.Score(
        my_optimizer.BestEncoding(100, self.videofile)))

  def test_BestEncodingOtherSpeedNoScore(self):
    my_optimizer = self.StdOptimizer()
    my_optimizer.BestEncoding(100, self.videofile).Execute().Store()
    self.assertIsNone(my_optimizer.BestEncoding(200, self.videofile).Result())

  def test_AutoGenerateClipTime(self):
    my_optimizer = optimizer.Optimizer(self.codec, self.file_set,
                                       cache_class=self.cache_class,
                                       score_function=ReturnsClipTime)
    my_encoder = encoder.Encoder(my_optimizer.context,
        encoder.OptionValueSet(encoder.OptionSet(), ''))
    # Must use a tricked-out videofile to avoid disk access.
    videofile = DummyVideofile('test_640x480_20.yuv', clip_time=1)
    my_encoding = encoder.Encoding(my_encoder, 123, videofile)
    my_encoding.result = {'psnr':42, 'bitrate':123}
    # If cliptime is not present, this will raise an exception.
    my_optimizer.Score(my_encoding)


class TestFileAndRateSet(unittest.TestCase):

  def test_OneFileAddedAndReturned(self):
    the_set = optimizer.FileAndRateSet()
    the_set.AddFilesAndRates(['filename'], [100], 'dirname')
    self.assertEqual([(100, 'dirname/filename')], the_set.AllFilesAndRates())

  def test_NoDirName(self):
    the_set = optimizer.FileAndRateSet()
    the_set.AddFilesAndRates(['filename'], [100])
    self.assertEqual([(100, 'filename')], the_set.AllFilesAndRates())

  def test_OneFileMultipleRates(self):
    the_set = optimizer.FileAndRateSet()
    the_set.AddFilesAndRates(['filename'], [100, 200], 'dirname')
    self.assertEqual(set([(100, 'dirname/filename'),
                          (200, 'dirname/filename')]),
                     set(the_set.AllFilesAndRates()))

  def test_TwoAddCalls(self):
    the_set = optimizer.FileAndRateSet()
    the_set.AddFilesAndRates(['filename'], [100, 200], 'dirname')
    the_set.AddFilesAndRates(['otherfilename'], [200, 300], 'dirname')
    self.assertEqual(set([(100, 'dirname/filename'),
                          (200, 'dirname/filename'),
                          (200, 'dirname/otherfilename'),
                          (300, 'dirname/otherfilename')]),
                     set(the_set.AllFilesAndRates()))

  def test_RatesForFile(self):
    the_set = optimizer.FileAndRateSet()
    the_set.AddFilesAndRates(['filename'], [100, 200])
    the_set.AddFilesAndRates(['otherfilename'], [200, 300])
    self.assertEqual(set([100, 200]),
                     set(the_set.AllRatesForFile('filename')))


if __name__ == '__main__':
  unittest.main()
