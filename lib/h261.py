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
"""H.261 codec.

This uses ffmpeg for encoding and decoding.
"""
import encoder
import ffmpeg

class H261Codec(ffmpeg.FfmpegCodec):
  def __init__(self, name='h261'):
    super(H261Codec, self).__init__(name)
    self.codecname = 'h261'
    self.extension = 'h261'

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(self.option_set, ''))

  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    # TODO(hta): Merge the common parts of this with vp8.Execute.
    commandline = (
      '%s %s -s %dx%d -i %s -codec:v %s -b:v %dk -y -s 352x288 %s' % (
        encoder.Tool('ffmpeg'),
        parameters.ToString(), videofile.width, videofile.height,
        videofile.filename, self.codecname,
        bitrate, encodedfile))
    return commandline

  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    # The special thing here is that it rescales back to the original size.
    commandline = "%s -i %s -s %sx%s %s" % (
      encoder.Tool('ffmpeg'),
      encodedfile, videofile.width, videofile.height,
      yuvfile)
    return commandline

