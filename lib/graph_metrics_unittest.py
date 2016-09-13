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
"""Unit tests for the graph_metrics module"""

import encoder
import fileset_picker
import graph_metrics
import optimizer
import score_tools
import test_tools
import unittest

class FakeCodec1(encoder.Codec):
  def __init__(self, name='mock1'):
    super(FakeCodec1, self).__init__(name)
    self.option_set = encoder.OptionSet()

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(self.option_set, ''))


class FakeCodec2(FakeCodec1):
  def __init__(self):
    super(FakeCodec2, self).__init__('mock2')
    self.option_set = encoder.OptionSet()


class TestBdRateAnalyzer(test_tools.FileUsingCodecTest):

  def test_EmptyDirectory(self):
    fileobject = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    with self.assertRaises(graph_metrics.NotEnoughDataError):
      graph_metrics.BdRateAnalysis(fileobject.filename,
                                   (FakeCodec1(), FakeCodec2()),
                                   score_tools.ScorePsnrBitrate)

  def test_LinearRegressionDifference(self):
    fileobject = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    fileset = optimizer.FileAndRateSet()
    fileset.AddFilesAndRates([fileobject.filename],
                             fileset_picker.ChooseRates(fileobject.width,
                                                        fileobject.framerate))
    context1 = encoder.Context(FakeCodec1(), encoder.EncodingDiskCache)
    encoder1 = context1.codec.StartEncoder(context1)
    # Produce two straight lines, one using 50% more bits than the others.
    for rate in fileset.AllRatesForFile(fileobject.filename):
      encoding = encoder1.Encoding(rate, fileobject)
      encoding.result = {'bitrate': rate, 'psnr': rate / 10}
      encoding.Store()
    context2 = encoder.Context(FakeCodec2(), encoder.EncodingDiskCache)
    encoder2 = context2.codec.StartEncoder(context2)
    for rate in fileset.AllRatesForFile(fileobject.filename):
      encoding = encoder2.Encoding(rate, fileobject)
      encoding.result = {'bitrate': rate * 1.5, 'psnr': rate / 10}
      encoding.Store()
    score = graph_metrics.BdRateAnalysis(fileobject.filename,
                                          (FakeCodec1(), FakeCodec2()),
                                          score_tools.ScorePsnrBitrate)
    self.assertEqual('mock2', score.score()[0][0])
    self.assertAlmostEqual(50.0, score.score()[0][1]['difference'])


if __name__ == '__main__':
  unittest.main()
