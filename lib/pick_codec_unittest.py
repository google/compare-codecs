#!/usr/bin/python
"""Tests for the codec picker."""

import unittest
import pick_codec

class TestPickCodec(unittest.TestCase):
  def test_DistinctWorkdirs(self):
    seenDirs = set()
    for codec_name in pick_codec.codec_map:
      codec = pick_codec.PickCodec(codec_name)
      self.assertNotIn(codec.cache.WorkDir(), seenDirs,
                       'Duplicate workdir for codec %s' % codec_name)
      seenDirs.add(codec.cache.WorkDir())

if __name__ == '__main__':
  unittest.main()
