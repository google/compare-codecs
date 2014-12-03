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
"""X264 codec definition.

This file defines how to run encode and decode for the x264 implementation
of H.264.
"""
import encoder
import file_codec

class X264Codec(file_codec.FileCodec):
  def __init__(self, name='x264', formatter=None):
    super(X264Codec, self).__init__(
      name,
      formatter=(formatter or encoder.OptionFormatter(prefix='--', infix=' ')))
    self.extension = 'mkv'
    self.option_set = encoder.OptionSet(
      encoder.Option('preset', ['ultrafast', 'superfast', 'veryfast',
                                'faster', 'fast', 'medium', 'slow', 'slower',
                                'veryslow', 'placebo']),
      encoder.Option('rc-lookahead', ['0', '30', '60']),
      encoder.Option('vbv-init', ['0.5', '0.8', '0.9']),
      encoder.Option('ref', ['1', '2', '3', '16']),
    )

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(
      self.option_set,
      '--rc-lookahead 0 --ref 2 --vbv-init 0.8 --preset veryslow',
      formatter=self.option_formatter))


  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    commandline = ('%(x264)s '
      '--vbv-maxrate %(bitrate)d --vbv-bufsize %(bitrate)d '
      '--bitrate %(bitrate)d --fps %(framerate)d '
      '--threads 1 '
      '--profile baseline --no-scenecut --keyint infinite '
      '--input-res %(width)dx%(height)d '
      '--tune psnr '
      '%(parameters)s '
      '-o %(outputfile)s %(inputfile)s') % {
        'x264': encoder.Tool('x264'),
        'bitrate': bitrate,
        'framerate': videofile.framerate,
        'width': videofile.width,
        'height': videofile.height,
        'outputfile': encodedfile,
        'inputfile': videofile.filename,
        'parameters': parameters.ToString()}
    return commandline


  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    commandline = '%s -i %s %s' % (encoder.Tool("ffmpeg"),
                                    encodedfile, yuvfile)
    return commandline

  def ResultData(self, encodedfile):
    more_results = {}
    more_results['frame'] = file_codec.MatroskaFrameInfo(encodedfile)
    return more_results
