#!/usr/bin/python
# Copyright 2015 Google.
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
"""Unit tests for the fileset picker. """
import os
import test_tools
import unittest

import fileset_picker


class TestFilesetPicker(unittest.TestCase):
  def testPickMpegFileset(self):
    fileset = fileset_picker.PickFileset('mpeg_video')
    self.assertEquals(44, len(fileset.AllFilesAndRates()))

  def testPickNonexistentFileset(self):
    with self.assertRaises(fileset_picker.Error):
      fileset_picker.PickFileset('no_such_directory')


class TestFilesetPickerWithLocalFiles(test_tools.FileUsingCodecTest):
  def testPickLocalVideoDirectory(self):
    os.mkdir(os.path.join(os.getenv('WORKDIR'), 'video'))
    os.mkdir(os.path.join(os.getenv('WORKDIR'), 'video', 'local'))
    test_tools.MakeYuvFileWithOneBlankFrame(
        'video/local/one_black_frame_1024_768_30.yuv')
    fileset = fileset_picker.PickFileset('local')
    self.assertEquals(4, len(fileset.AllFilesAndRates()))


if __name__ == '__main__':
  unittest.main()
