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
import encoder_configuration
import optimizer

def InitWorkDir():
  dirname = tempfile.mkdtemp(prefix='codec-unittest-workdir')
  if not os.path.isdir(dirname):
    os.mkdir(dirname)
  os.mkdir(dirname + '/workdir')
  encoder_configuration.conf.override_workdir_for_test(dirname +
                                                       '/workdir')
  encoder_configuration.conf.override_sysdir_for_test(dirname)
  encoder_configuration.conf.override_scorepath_for_test([])
  return dirname

def MakeYuvFileWithBlankFrames(name, count):
  """Make an YUV file with one or more blank frames (all zeroes).

  The size of the frame is encoded in the filename."""
  videofile = encoder.Videofile('%s/%s' % (encoder_configuration.conf.workdir(),
                                           name))
  # Frame size in an YUV 4:2:0 file is 1.5 bytes per pixel.
  framesize = videofile.width * videofile.height * 3 / 2
  with open(videofile.filename, 'w') as real_file:
    real_file.write('\0' * framesize * count)
  return videofile

def MakeYuvFileWithNoisyFrames(name, count):
  """Make an YUV file with one or more frames containing noise."""
  videofile = encoder.Videofile('%s/%s' % (encoder_configuration.conf.workdir(),
                                           name))
  # Frame size in an YUV 4:2:0 file is 1.5 bytes per pixel.
  framesize = videofile.width * videofile.height * 3 / 2
  with open(videofile.filename, 'w') as real_file:
    for frameno in xrange(count):
      for videobyte in xrange(framesize):
        real_file.write(str(chr((frameno + videobyte) % 256)))
  return videofile

def MakeYuvFileWithOneBlankFrame(name):
  """Make an YUV file with one black frame."""
  return MakeYuvFileWithBlankFrames(name, 1)

def EmptyWorkDirectory():
  dirname = encoder_configuration.conf.workdir()
  if dirname[0:4] != '/tmp':
    raise encoder.Error('Workdir is %s, not a tempfile' % dirname)
  shutil.rmtree(dirname)
  os.mkdir(dirname)

def FinishWorkDir(dirname):
  # Verification of validity
  if encoder_configuration.conf.sysdir() != dirname:
    raise encoder.Error('Dirname was wrong in FinishWorkDir')
  shutil.rmtree(dirname)

def TestFileSet():
  """Returns a file set containing a file with one black frame.

  Creates the file as a side effect."""

  the_set = optimizer.FileAndRateSet()
  filename = 'one_black_frame_1024_768_30.yuv'
  MakeYuvFileWithOneBlankFrame(filename)
  my_directory = encoder_configuration.conf.workdir()
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

  def setUp(self):
    encoder_configuration.conf.override_scorepath_for_test([])
