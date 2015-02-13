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
"""Framework for specifying encoders from ffmpeg.

This uses ffmpeg for encoding and decoding.
The default FFMPEG encoder uses mpeg4, so that we can see if it's roughly
compatible with the vpxenc-produced qualities.
"""
import ast
import os
import subprocess

import encoder
import file_codec


class HevcCodec(file_codec.FileCodec):

  def __init__(self,
               name='hevc',
               formatter=None):
    self.name = name
    self.codecname = 'hevc'
    self.extension = 'hevc'
    super(HevcCodec, self).__init__(
      name,
      formatter=formatter)

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(self.option_set, ''))

  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    commandline = (
        '%s --SourceWidth=%d ---SourceHeight=%d '
        '-c %s '
        '--FrameRate=%d --InputFile=%s '
        '--FramesToBeEncoded=%d '
        '--IntraPeriod=-1 '
        '%s --TargetBitrate=%d --BitstreamFile=%s' % (
            encoder.Tool('TAppEncoderStatic'),
            videofile.width, videofile.height,
            encoder.Tool('hevc_ra_main.cfg'),  # Configuration file
            videofile.framerate,
            videofile.filename,
            videofile.FrameCount(),
            parameters.ToString(),
            bitrate, encodedfile))
    return commandline

  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    commandline = "%s --BitstreamFile=%s --ReconFile=%s" % (
        encoder.Tool('TAppDecoderStatic'),
        encodedfile, yuvfile)
    return commandline
