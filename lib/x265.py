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
"""X265 codec definitions.

This gives the definitions required to run the x265 implementation of
the HEVC codec.
"""
import encoder
import ffmpeg


class X265Codec(ffmpeg.FfmpegCodec):
  def __init__(self, name='x265'):
    # The x265 encoder uses default parameter delimiters, unlike
    # the ffmpeg family; we inherit the decoding process.
    super(X265Codec, self).__init__(name,
                                    formatter=encoder.OptionFormatter())
    self.extension = 'hevc'
    self.codecname = 'hevc'
    self.option_set = encoder.OptionSet()

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(self.option_set,
        ''))

  def ConfigurationFixups(self, config):
    # No fixups so far.
    return config

  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    commandline = ('%(x265)s '
        '--bitrate %(bitrate)d --fps %(framerate)d '
        '--threads 1 '
        '--input-res %(width)dx%(height)d '
        '%(parameters)s '
        '-o %(outputfile)s %(inputfile)s') % {
            'x265': encoder.Tool('x265'),
            'bitrate': bitrate,
            'framerate': videofile.framerate,
            'width': videofile.width,
            'height': videofile.height,
            'outputfile': encodedfile,
            'inputfile': videofile.filename,
            'parameters': parameters.ToString()}
    return commandline

  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    # Because of a bug in the ffmpeg decoder, we're using JM decoder.
    # ffmpeg sometimes produces a decoded YUV file slightly shorter
    # than the expected size.
    commandline = '%s -b %s -o %s' % (encoder.Tool('TAppDecoderStatic'),
                                      encodedfile,
                                      yuvfile)
    return commandline
