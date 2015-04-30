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
"""Configuration for the encoder and related functions.

This module contains the code for reading the configuration from environment
variables, and setters for overriding that configuration in tests.
"""
import os


class Configuration(object):
  def __init__(self):
    self.work_directory = os.environ['CODEC_WORKDIR']
    self.sys_directory = os.environ['WORKDIR']
    self.tool_directory = os.environ['CODEC_TOOLPATH']

  def workdir(self):
    return self.work_directory

  def sysdir(self):
    return self.sys_directory

  def tooldir(self):
    return self.tool_directory

  def override_workdir_for_test(self, test_workdir):
    self.work_directory = test_workdir

  def override_sysdir_for_test(self, test_sysdir):
    self.sys_directory = test_sysdir

# A static variable for holding the current configuration.
# pylint: disable=invalid-name
conf = Configuration()
