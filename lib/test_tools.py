#!/usr/bin/python
#
# Tools for unittests that require storing video files on disk.
#
import os
import shutil
import tempfile
import unittest

import encoder

def InitWorkDir():
  dirname = tempfile.mkdtemp(prefix='codec-unittest-workdir')
  if not os.path.isdir(dirname):
    os.mkdir(dirname)
  os.environ['CODEC_WORKDIR'] = dirname
  return dirname

def MakeYuvFileWithOneBlankFrame(name):
  """ Make an YUV file with one black frame.
  The size of the frame is encoded in the filename."""
  videofile = encoder.Videofile('%s/%s' % (os.getenv('CODEC_WORKDIR'),
                                           name))
  # Frame size in an YUV 4:2:0 file is 1.5 bytes per pixel.
  framesize = videofile.width * videofile.height * 3 / 2
  with open(videofile.filename, 'w') as real_file:
    real_file.write('\0' * framesize)
  return videofile

def FinishWorkDir(dirname):
  # Verification of validity
  if os.environ['CODEC_WORKDIR'] != dirname:
    raise encoder.Error('Dirname was wrong in FinishWorkDir')
  shutil.rmtree(dirname)

class FileUsingCodecTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls._workdir = InitWorkDir()
  
  @classmethod
  def tearDownClass(cls):
    FinishWorkDir(cls._workdir)


