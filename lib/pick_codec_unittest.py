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
"""Tests for the codec picker.
This file is also the place for tests that cover several codecs."""

import os
import unittest

import encoder
import pick_codec

class TestPickCodec(unittest.TestCase):
  def test_DistinctWorkdirs(self):
    seenDirs = set()
    for codec_name in pick_codec.codec_map:
      codec = pick_codec.PickCodec(codec_name)
      context = encoder.Context(codec)
      workdir = os.path.abspath(context.cache.WorkDir())
      self.assertNotIn(workdir, seenDirs,
                       'Duplicate workdir %s for codec %s' %
                       (workdir, codec_name))
      seenDirs.add(workdir)


if __name__ == '__main__':
  unittest.main()
