#!/usr/bin/python
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
