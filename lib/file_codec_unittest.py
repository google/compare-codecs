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

class TestFileCodec(test_tools.FileUsingCodecTest):

  def test_OneBlackFrame(self):
    codec = CopyingCodec()
    videofile = test_tools.MakeYuvFileWithOneBlankFrame(
      'one_black_frame_1024_768_30.yuv')
    encoding = codec.BestEncoding(1000, videofile)
    encoding.Execute()
    self.assertTrue(encoding.Score())

if __name__ == '__main__':
  unittest.main()
