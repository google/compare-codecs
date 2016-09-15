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
"""VP9 codec definitions.

This is an instance of a codec definition.
It tells the generic codec the following:
- Name of codec = directory of codec database
- File extension
- Options table
"""
import encoder
import file_codec
import re
import subprocess

class Vp9Codec(file_codec.FileCodec):
  def __init__(self, name='vp9'):
    super(Vp9Codec, self).__init__(name)
    self.extension = 'webm'
    self.option_set = encoder.OptionSet(
      encoder.IntegerOption('cpu-used', 0, 8),
      # The "best" option gives encodes that are too slow to be useful.
      encoder.ChoiceOption(['good', 'rt']).Mandatory(),
      encoder.IntegerOption('passes', 1, 2),
      encoder.IntegerOption('aq-mode', 0, 4),
      encoder.Option('end-usage', ['cbr', 'vbr', 'cq', 'q']),
    )

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(self.option_set,
        '--passes=1 --good --noise-sensitivity=0 --cpu-used=5'))

  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    commandline = (encoder.Tool('vpxenc') + ' ' + parameters.ToString()
                   + ' --target-bitrate=' + str(bitrate)
                   + ' --fps=' + str(videofile.framerate) + '/1'
                   + ' -w ' + str(videofile.width)
                   + ' -h ' + str(videofile.height)
                   + ' ' + videofile.filename
                   + ' --codec=vp9 '
                   + ' -o ' + encodedfile)
    return commandline

  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    commandline = '%s %s --i420 -o %s' % (encoder.Tool("vpxdec"),
                                    encodedfile, yuvfile)
    return commandline

  def ResultData(self, encodedfile):
    more_results = {}
    more_results['frame'] = file_codec.MatroskaFrameInfo(encodedfile)
    return more_results

  def EncoderVersion(self):
    # The vpxenc command line tool outputs the version number of the
    # encoder as part of its error message on illegal arguments.
    try:
      subprocess.check_output([encoder.Tool('vpxenc')],
                              stderr=subprocess.STDOUT)
    except Exception, err:
      version_output = str(err.output)
      for line in version_output.split('\n'):
        match = re.match(r'\s+vp9\s+- (.+)$', line)
        if match:
          return match.group(1)
      raise encoder.Error('Did not find vp9 version string')
    raise encoder.Error('Getting vp9 version from help message failed')
