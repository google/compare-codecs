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
"""Unit tests for the FileCodec framework"""

import encoder
import optimizer
import test_tools
import time
import unittest
import vp8

import file_codec

class CopyingCodec(file_codec.FileCodec):
  """A "codec" that works by copying the file."""
  def __init__(self, name='copy'):
    super(CopyingCodec, self).__init__(name)
    self.extension = 'yuv'

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(None, ''))

  def EncodeCommandLine(self, parameters, bitrate, videofile, outputfile):
    return 'cp %s %s' % (videofile.filename, outputfile)

  def DecodeCommandLine(self, videofile, inputfile, outputfile):
    return 'cp %s %s' % (inputfile, outputfile)

class CorruptingCodec(file_codec.FileCodec):
  """A "codec" that gives a different result every time."""
  def __init__(self, name='corrupt'):
    super(CorruptingCodec, self).__init__(name)
    self.extension = 'yuv'

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(None, ''))

  def EncodeCommandLine(self, parameters, bitrate, videofile, outputfile):
    # Fill the outputfile with the date in nanoseconds.
    return 'date +%%N > %s' % outputfile

  def DecodeCommandLine(self, videofile, inputfile, outputfile):
    # pylint: disable=W0613
    # We make the codec "work" by copying from the original file
    # as a decode.
    return 'cp %s %s' % (videofile.filename, outputfile)
 

class TestFileCodec(test_tools.FileUsingCodecTest):

  def test_OneBlackFrame(self):
    codec = CopyingCodec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    self.assertTrue(encoding.Result())

  def test_VerifyOneBlackFrame(self):
    codec = CopyingCodec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    self.assertTrue(encoding.VerifyEncode())

  def test_VerifyCorruptedFile(self):
    codec = CorruptingCodec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    self.assertFalse(encoding.VerifyEncode())

  def test_VerifyMatroskaFile(self):
    codec = vp8.Vp8Codec()
    my_optimizer = optimizer.Optimizer(codec)
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
        'one_black_frame_1024_768_30.yuv')
    encoding = my_optimizer.BestEncoding(1000, videofile)
    encoding.Execute()
    # Matroska files will be identical if generated within the same
    # clock second. So wait a bit.
    time.sleep(1)
    self.assertTrue(encoding.VerifyEncode())


if __name__ == '__main__':
  unittest.main()
