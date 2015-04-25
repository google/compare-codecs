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
"""X264 baseline codec definition.

This file defines how to run encode and decode for the x264 implementation
of H.264 using the Baseline profile.
"""
import encoder
import x264


class X264BaselineCodec(x264.X264Codec):
  def __init__(self, name='x264-base', formatter=None):
    super(X264BaselineCodec, self).__init__(name, formatter)
    self.option_set.LockOption('profile', 'baseline')

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(
      self.option_set,
      '--profile baseline --preset slow --tune psnr --threads 1',
      formatter=self.option_formatter))
