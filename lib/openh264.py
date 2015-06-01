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
"""Invoker for the openh264 encoder."""
import encoder
import file_codec
import os


class OpenH264Codec(file_codec.FileCodec):

  def __init__(self,
               name='openh264',
               formatter=None):
    self.name = name
    self.codecname = 'openh264'
    super(OpenH264Codec, self).__init__(
      name,
      formatter=formatter or encoder.OptionFormatter(prefix='-', infix=' '))
    self.extension = '264'
    self.option_set = encoder.OptionSet(
      # Rate control. -1 = off, 0 = quality, 1 = bitrate, 2 = buffer based
      # Default is set in config file by RCMode parameter to 0.
      # Only 0 and 1 really make sense when rate control is used to select
      # the bitrate target.
      encoder.Option('rc', ['0', '1'])
    )

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(self.option_set, ''))

  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    # The openh264 configuration file system requires that one executes
    # in the tool directory.
    commandline = (
        'cd %s && %s %s '
        '-org %s '
        '-bf %s '
        '-sw %d -sh %d '
        '-dw 0 %d -dh 0 %d '
        '-maxbrTotal 0 -tarb %d '
        '-ltarb 0 %d '
        '-lmaxb 0 0 '
        '-numtl 1 '
        '-frin %d -frout 0 %d ' #this is to set the frame rate
        '-fs 0 ' #disable FrameSkip with this option
        '-aq 0 ' #disable AdaptiveQuantizaion with this option
        '%s ' % (
            encoder.Tool('.'),
            encoder.Tool('h264enc'),
            encoder.Tool('openh264.cfg'),  # Configuration file
            os.path.join(os.getenv('WORKDIR'), videofile.filename),
            encodedfile,
            videofile.width, videofile.height,
            videofile.width, videofile.height,
            bitrate,
            bitrate,
            videofile.framerate, videofile.framerate,
            parameters.ToString()))
    return commandline

  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    commandline = '%s %s %s' % (encoder.Tool("h264dec"),
                                    encodedfile, yuvfile)
    return commandline

  def ResultData(self, encodedfile):
    more_results = {}
    more_results['frame'] = file_codec.FfmpegFrameInfo(encodedfile)
    return more_results
