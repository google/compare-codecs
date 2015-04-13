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
"""Motion JPEG codec.

This uses ffmpeg for encoding and decoding.
"""
import encoder
import ffmpeg

class MotionJpegCodec(ffmpeg.FfmpegCodec):
  def __init__(self, name='mjpeg'):
    super(MotionJpegCodec, self).__init__(name)
    self.codecname = 'mjpeg'
    self.extension = 'mjpeg'
    self.option_set = encoder.OptionSet(
      encoder.IntegerOption('qmin', 1, 69),
      encoder.IntegerOption('qmax', 2, 1024),
    )

  def StartEncoder(self, context):
    return encoder.Encoder(
      context, encoder.OptionValueSet(self.option_set, '',
                                      formatter=self.option_formatter))

  def ConfigurationFixups(self, config):
    """Ensure that qmin is less than qmax."""
    if config.HasValue('qmin'):
      qmin = int(config.GetValue('qmin'))
    else:
      qmin = self.option_set.Option('qmin').min

    if config.HasValue('qmax'):
      qmax = int(config.GetValue('qmax'))
    else:
      # It seems that the default for qmax is rather low - at least, there's
      # an error saying "qmax is too low" when only -qmin 39 is given.
      # From manual probing: qmin 31 succeeds, qmin 32 fails.
      qmax = 31

    if qmax < qmin:
      return config.ChangeValue('qmax', str(qmin))
    return config
