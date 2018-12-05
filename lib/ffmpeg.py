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
"""Framework for specifying encoders from ffmpeg.

This uses ffmpeg for encoding and decoding.
The default FFMPEG encoder uses mpeg4, so that we can see if it's roughly
compatible with the vpxenc-produced qualities.
"""
import encoder
import file_codec
import re
import subprocess

class FfmpegCodec(file_codec.FileCodec):

  def __init__(self,
               name='ffmpeg-mpeg4',
               formatter=None):
    self.name = name
    self.codecname = 'mpeg4'
    self.extension = 'avi'
    super(FfmpegCodec, self).__init__(
      name,
      formatter=(formatter or encoder.OptionFormatter(prefix='-', infix=' ')))

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(self.option_set, ''))

  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    commandline = (
      '%s -loglevel warning -s %dx%d -i %s -codec:v %s %s -b:v %dk -y %s' % (
        encoder.Tool('ffmpeg'),
        videofile.width, videofile.height,
        videofile.filename, self.codecname,
        parameters.ToString(),
        bitrate, encodedfile))
    return commandline

  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    commandline = "%s -loglevel warning -codec:v %s -i %s %s" % (
      encoder.Tool('ffmpeg'),
      self.codecname,
      encodedfile, yuvfile)
    return commandline

  def ResultData(self, encodedfile):
    return {'frame': file_codec.FfmpegFrameInfo(encodedfile)}

  def EncoderVersion(self):
    version_output = subprocess.check_output([encoder.Tool('ffmpeg'),
                                              '-version'])
    match = re.match('(ffmpeg .*) Copyright', version_output)
    if match:
      return match.group(0)
    raise encoder.Error('ffmpeg did not find its version string')
