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
"""Unit tests for encoder_configuration."""

import os
import unittest
import encoder_configuration


class TestConfiguration(unittest.TestCase):
  def test_defaults(self):
    # These tests verify reading from the current environment.
    # They should work no matter what the variables are set to,
    # as long as required variables are set.
    self.assertEquals(os.environ['CODEC_WORKDIR'],
                      encoder_configuration.conf.workdir())
    self.assertEquals(os.environ['WORKDIR'],
                      encoder_configuration.conf.sysdir())
    self.assertEquals(os.environ['CODEC_TOOLPATH'],
                      encoder_configuration.conf.tooldir())
    self.assertEquals(os.getenv('CODEC_SCOREPATH', ''),
                      ':'.join(encoder_configuration.conf.scorepath()))

  def test_scorepath_variants(self):
    # This test works by modifying the environment and then creating
    # a new configuration object. It does not use the global configuration
    # object.
    if 'CODEC_SCOREPATH' in os.environ:
      del os.environ['CODEC_SCOREPATH']
    os.environ['CODEC_WORKDIR'] = 'strange_string'
    my_conf = encoder_configuration.Configuration()
    self.assertEquals(0, len(my_conf.scorepath()))
    os.environ['CODEC_SCOREPATH'] = 'a:b'
    my_conf = encoder_configuration.Configuration()
    self.assertEquals('a and b', ' and '.join(my_conf.scorepath()))

  def test_override(self):
    encoder_configuration.conf.override_workdir_for_test('new_value')
    self.assertEquals('new_value',
                      encoder_configuration.conf.workdir())


if __name__ == '__main__':
  unittest.main()
