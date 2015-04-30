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
    self.assertEquals(os.environ['CODEC_WORKDIR'],
                      encoder_configuration.conf.workdir())
    self.assertEquals(os.environ['WORKDIR'],
                      encoder_configuration.conf.sysdir())
    self.assertEquals(os.environ['CODEC_TOOLPATH'],
                      encoder_configuration.conf.tooldir())

  def test_override(self):
    encoder_configuration.conf.override_workdir_for_test('new_value')
    self.assertEquals('new_value',
                      encoder_configuration.conf.workdir())


if __name__ == '__main__':
  unittest.main()
