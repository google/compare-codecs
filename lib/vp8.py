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
"""VP8 codec definitions.

This is an instance of a codec definition.
It tells the generic codec the following:
- Name of codec = directory of codec database
- File extension
- Options table
"""
import encoder
import file_codec

class Vp8Codec(file_codec.FileCodec):
  def __init__(self, name='vp8'):
    super(Vp8Codec, self).__init__(name)
    self.extension = 'webm'
    self.option_set = encoder.OptionSet(
      encoder.Option('overshoot-pct', ['0', '15', '30', '45']),
      encoder.Option('undershoot-pct', ['0', '25', '50', '75', '100']),
      # CQ mode is not considered for end-usage at the moment.
      encoder.Option('end-usage', ['cbr', 'vbr']),
      # End-usage cq doesn't really make sense unless we also set q to something
      # between min and max. This is being checked.
      # encoder.Option('end-usage', ['cbr', 'vbr', 'cq']),
      encoder.Option('end-usage', ['cbr', 'vbr']),
      encoder.Option('min-q', ['0', '2', '4', '8', '16', '24']),
      encoder.Option('max-q', ['32', '56', '63']),
      encoder.Option('buf-sz', ['200', '500', '1000', '2000', '4000',
                                '8000', '16000']),
      encoder.Option('buf-initial-sz', ['200', '400', '800', '1000', '2000',
                                        '4000', '8000', '16000']),
      encoder.Option('max-intra-rate', ['100', '200', '400', '600', '800',
                                        '1200']),
      encoder.ChoiceOption(['good', 'best', 'rt']),
      encoder.IntegerOption('cpu-used', -16, 16),
    )

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(self.option_set,
      '--lag-in-frames=0 '
      '--kf-min-dist=3000 '
      '--kf-max-dist=3000 --cpu-used=0 --static-thresh=0 '
      '--token-parts=1 --end-usage=cbr --min-q=2 --max-q=56 '
      '--undershoot-pct=100 --overshoot-pct=15 --buf-sz=1000 '
      '--buf-initial-sz=800 --buf-optimal-sz=1000 --max-intra-rate=1200 '
      '--resize-allowed=0 --drop-frame=0 '
      '--passes=1 --good --noise-sensitivity=0'))

  def ConfigurationFixups(self, config):
    # In RT mode, vp8 will change encoding based on elapsed time if
    # cpu-used is positive, thus making encodings unstable.
    # Negative values give stable encodings, with -1
    # being the slowest variant.
    if config.HasValue('good/best/rt'):
      if config.GetValue('good/best/rt') == 'rt':
        if (not config.HasValue('cpu-used')
            or int(config.GetValue('cpu-used')) >= 0):
          return config.ChangeValue('cpu-used', '-1')
    return config

  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    commandline = (encoder.Tool('vpxenc') + ' ' + parameters.ToString()
                   + ' --target-bitrate=' + str(bitrate)
                   + ' --fps=' + str(videofile.framerate) + '/1'
                   + ' -w ' + str(videofile.width)
                   + ' -h ' + str(videofile.height)
                   + ' ' + videofile.filename
                   + ' --codec=vp8 '
                   + ' -o ' + encodedfile)
    return commandline

  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    commandline = '%s -i %s %s' % (encoder.Tool("ffmpeg"),
                                    encodedfile, yuvfile)
    return commandline

  def ResultData(self, encodedfile):
    more_results = {}
    more_results['frame'] = file_codec.MatroskaFrameInfo(encodedfile)
    return more_results
