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
# Tools for unittests that require storing video files on disk.
#
import os
import shutil
import tempfile
import unittest

import encoder
import optimizer

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

def TestFileSet():
  """Returns a file set containing a file with one black frame.

  Creates the file as a side effect."""

  the_set = optimizer.FileAndRateSet()
  filename = 'one_black_frame_1024_768_30.yuv'
  MakeYuvFileWithOneBlankFrame(filename)
  my_directory = os.environ['CODEC_WORKDIR']
  the_set.AddFilesAndRates([filename],
                           [300, 1000, 3000],
                           my_directory)
  return the_set

class FileUsingCodecTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls._workdir = InitWorkDir()
  
  @classmethod
  def tearDownClass(cls):
    FinishWorkDir(cls._workdir)


