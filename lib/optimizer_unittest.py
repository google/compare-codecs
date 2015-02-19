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

""" Unit tests for the optimizer. """
import os
import re
import unittest

import encoder
import optimizer
import test_tools

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


class TestOptimizer(unittest.TestCase):
  def setUp(self):
    self.codec = DummyCodec()
    self.file_set = None
    self.cache_class = encoder.EncodingMemoryCache
    self.score_function = None
    self.videofile = DummyVideofile('foofile_640_480_30.yuv', clip_time=1)
    self.optimizer = None

  def StdOptimizer(self):
    # This function is not in setup because some tests
    # do not need it.
    if not self.optimizer:
      self.optimizer = optimizer.Optimizer(self.codec, self.file_set,
                                           cache_class=self.cache_class)
    return self.optimizer

  def EncoderFromParameterString(self, parameter_string):
    return encoder.Encoder(self.optimizer.context,
        encoder.OptionValueSet(self.optimizer.context.codec.option_set,
                               parameter_string))

  def testInit(self):
    optimizer.Optimizer(self.codec, self.file_set,
                        cache_class=self.cache_class)

  def test_AlternateScorer(self):
    my_optimizer = optimizer.Optimizer(self.codec, self.file_set,
                                       cache_class=self.cache_class,
                                       score_function=Returns1)
    my_optimizer.BestEncoding(100, self.videofile).Execute().Store()
    self.assertAlmostEqual(1,
        my_optimizer.Score(my_optimizer.BestEncoding(100, self.videofile)),
        places=4)

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
    self.assertAlmostEqual(5, my_optimizer.Score(
        my_optimizer.BestEncoding(100, self.videofile)),
        places=4)

  def test_BestEncodingOtherSpeedNoScore(self):
    my_optimizer = self.StdOptimizer()
    my_optimizer.BestEncoding(100, self.videofile).Execute().Store()
    self.assertIsNone(my_optimizer.BestEncoding(200, self.videofile).Result())

  def test_BestUntriedEncodingReturnsSomething(self):
    my_optimizer = self.StdOptimizer()
    first_encoding = my_optimizer.BestEncoding(100, self.videofile)
    first_encoding.Execute().Store()
    other_encoding = my_optimizer.BestUntriedEncoding(100, self.videofile)
    self.assertTrue(other_encoding)
    self.assertNotEqual(first_encoding.encoder.parameters.ToString(),
                        other_encoding.encoder.parameters.ToString())

  def test_WorksBetterOnSomeOtherClip(self):
    my_optimizer = self.StdOptimizer()
    videofile2 = DummyVideofile('barfile_640_480_30.yuv', clip_time=1)
    # Note - may have to do deterministic generation of these.
    encoder1 = self.EncoderFromParameterString('--score=5') # Low score
    encoder2 = self.EncoderFromParameterString('--score=10') # High score
    # Store 2 scores for the second videofile.
    encoding = encoder1.Encoding(100, videofile2)
    encoding.Execute().Store()
    encoding = encoder2.Encoding(100, videofile2)
    encoding.Execute().Store()
    # Store 1 score for the first videofile
    first_encoding = encoder1.Encoding(100, self.videofile)
    first_encoding.Execute().Store()
    # pylint: disable=W0212
    second_encoding = my_optimizer._WorksBetterOnSomeOtherClip(first_encoding,
                                                               100,
                                                               self.videofile)
    self.assertTrue(second_encoding)
    second_encoding.Execute()
    self.assertEquals(first_encoding.videofile, second_encoding.videofile)
    self.assertAlmostEqual(10, my_optimizer.Score(second_encoding),
                           places=4)

  def test_ShorterParameterListsScoreHigher(self):
    my_optimizer = self.StdOptimizer()
    encoder1 = self.EncoderFromParameterString('--score=5')
    encoder2 = self.EncoderFromParameterString(
      '--score=5 --another_parameter=yes')
    encoding1 = encoder1.Encoding(100, self.videofile)
    encoding1.Execute()
    encoding2 = encoder2.Encoding(100, self.videofile)
    encoding2.Execute()
    self.assertGreater(my_optimizer.Score(encoding1),
                       my_optimizer.Score(encoding2))

  def test_EncodingWithOneLessParameter(self):
    my_optimizer = self.StdOptimizer()
    my_encoder = self.EncoderFromParameterString('--score=5')
    first_encoding = my_encoder.Encoding(100, self.videofile)
    # pylint: disable=W0212
    next_encoding = my_optimizer._EncodingWithOneLessParameter(first_encoding,
                                                              100,
                                                              self.videofile,
                                                              None)
    self.assertTrue(next_encoding)
    self.assertEqual(next_encoding.encoder.parameters.ToString(), '')

  def test_EncodingGoodOnOtherRate(self):
    self.file_set = optimizer.FileAndRateSet(verify_files_present=False)
    self.file_set.AddFilesAndRates([self.videofile.filename], [100, 200])
    my_optimizer = self.StdOptimizer()
    my_encoder = self.EncoderFromParameterString('--score=7')
    my_encoder.Encoding(100, self.videofile).Execute().Store()
    first_encoder = self.EncoderFromParameterString('--score=8')
    first_encoding = first_encoder.Encoding(200, self.videofile)
    first_encoding.Execute().Store()
    # pylint: disable=W0212
    next_encoding = my_optimizer._EncodingGoodOnOtherRate(first_encoding,
                                                          200,
                                                          self.videofile,
                                                          None)
    self.assertTrue(next_encoding)
    self.assertEqual('--score=7', next_encoding.encoder.parameters.ToString())

  def test_BestOverallConfiguration(self):
    self.file_set = optimizer.FileAndRateSet(verify_files_present=False)
    self.file_set.AddFilesAndRates([self.videofile.filename], [100, 200])
    my_optimizer = self.StdOptimizer()
    # When there is nothing in the database, None should be returned.
    best_encoder = my_optimizer.BestOverallEncoder()
    self.assertIsNone(best_encoder)
    # Fill in the database with all the files and rates.
    my_encoder = self.EncoderFromParameterString('--score=7')
    for rate, filename in self.file_set.AllFilesAndRates():
      my_encoder.Encoding(rate, encoder.Videofile(filename)).Execute().Store()
    best_encoder = my_optimizer.BestOverallEncoder()
    self.assertTrue(best_encoder)
    self.assertEquals(my_encoder.parameters.ToString(),
                      best_encoder.parameters.ToString())
    # Add an incomplete encode. This should be ignored.
    (self.EncoderFromParameterString('--score=9')
        .Encoding(100, self.videofile).Execute().Store())
    best_encoder = my_optimizer.BestOverallEncoder()
    self.assertTrue(best_encoder)
    self.assertEquals(my_encoder.parameters.ToString(),
                      best_encoder.parameters.ToString())
     #  Complete the set for 'score=9'. This should cause a change.
    (self.EncoderFromParameterString('--score=9')
        .Encoding(200, self.videofile).Execute().Store())
    best_encoder = my_optimizer.BestOverallEncoder()
    self.assertTrue(best_encoder)
    self.assertEquals('--score=9',
                      best_encoder.parameters.ToString())


class TestFileAndRateSet(unittest.TestCase):

  def test_OneFileAddedAndReturned(self):
    the_set = optimizer.FileAndRateSet(verify_files_present=False)
    the_set.AddFilesAndRates(['filename'], [100], 'dirname')
    self.assertEqual([(100, 'dirname/filename')], the_set.AllFilesAndRates())

  def test_NoDirName(self):
    the_set = optimizer.FileAndRateSet(verify_files_present=False)
    the_set.AddFilesAndRates(['filename'], [100])
    self.assertEqual([(100, 'filename')], the_set.AllFilesAndRates())

  def test_OneFileMultipleRates(self):
    the_set = optimizer.FileAndRateSet(verify_files_present=False)
    the_set.AddFilesAndRates(['filename'], [100, 200], 'dirname')
    self.assertEqual(set([(100, 'dirname/filename'),
                          (200, 'dirname/filename')]),
                     set(the_set.AllFilesAndRates()))

  def test_TwoAddCalls(self):
    the_set = optimizer.FileAndRateSet(verify_files_present=False)
    the_set.AddFilesAndRates(['filename'], [100, 200], 'dirname')
    the_set.AddFilesAndRates(['otherfilename'], [200, 300], 'dirname')
    self.assertEqual(set([(100, 'dirname/filename'),
                          (200, 'dirname/filename'),
                          (200, 'dirname/otherfilename'),
                          (300, 'dirname/otherfilename')]),
                     set(the_set.AllFilesAndRates()))

  def test_RatesForFile(self):
    the_set = optimizer.FileAndRateSet(verify_files_present=False)
    the_set.AddFilesAndRates(['filename'], [100, 200])
    the_set.AddFilesAndRates(['otherfilename'], [200, 300])
    self.assertEqual(set([100, 200]),
                     set(the_set.AllRatesForFile('filename')))


class TestFileAndRateSetWithRealFiles(test_tools.FileUsingCodecTest):
  def test_AddMissingFile(self):
    the_set = optimizer.FileAndRateSet()
    the_set.AddFilesAndRates(['nosuchfile'], [100])
    self.assertFalse(the_set.AllFilesAndRates())
    self.assertFalse(the_set.set_is_complete)

  def test_AddPresentFile(self):
    the_set = optimizer.FileAndRateSet()
    file_name = 'file_1024_768_30.yuv'
    test_tools.MakeYuvFileWithOneBlankFrame(file_name)
    the_set.AddFilesAndRates([file_name], [100],
                             basedir=os.getenv('CODEC_WORKDIR'))
    self.assertTrue(the_set.AllFilesAndRates())
    self.assertTrue(the_set.set_is_complete)


if __name__ == '__main__':
  unittest.main()
