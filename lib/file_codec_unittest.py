#!/usr/bin/python
"""Unit tests for the FileCodec framework"""

import encoder
import test_tools
import unittest

import file_codec

class CopyingCodec(file_codec.FileCodec):
  """A "codec" that works by copying the file."""
  def __init__(self, name='copy'):
    super(CopyingCodec, self).__init__(name)
    self.extension = 'yuv'

  def StartEncoder(self):
    return encoder.Encoder(self, encoder.OptionValueSet(None, ''))

  def EncodeCommandLine(self, parameters, bitrate, videofile, outputfile):
    return 'cp %s %s' % (videofile.filename, outputfile)

  def DecodeCommandLine(self, videofile, inputfile, outputfile):
    return 'cp %s %s' % (inputfile, outputfile)

class CorruptingCodec(file_codec.FileCodec):
  """A "codec" that gives a different result every time."""
  def __init__(self, name='corrupt'):
    super(CorruptingCodec, self).__init__(name)
    self.extension = 'yuv'

  def StartEncoder(self):
    return encoder.Encoder(self, encoder.OptionValueSet(None, ''))

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
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = codec.BestEncoding(1000, videofile)
    encoding.Execute()
    self.assertTrue(encoding.Score())

  def test_VerifyOneBlackFrame(self):
    codec = CopyingCodec()
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = codec.BestEncoding(1000, videofile)
    encoding.Execute()
    self.assertTrue(encoding.VerifyEncode())

  def test_VerifyCorruptedFile(self):
    codec = CorruptingCodec()
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = codec.BestEncoding(1000, videofile)
    encoding.Execute()
    self.assertFalse(encoding.VerifyEncode())

if __name__ == '__main__':
  unittest.main()
