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

This constraint set operates in fixed QP mode.

It works by setting fixed-q, gold-q and key-q to given fixed values.
This requires a patch to the vpxenc binary.
"""
import encoder
import vp8


class Vp8CodecMpegMode(vp8.Vp8Codec):
  def __init__(self, name='vp8-mpeg'):
    super(Vp8CodecMpegMode, self).__init__(name)
    # Set the parts that are different from the VP8 codec.
    self.option_set = encoder.OptionSet(
      encoder.IntegerOption('fixed-q', 0, 63).Mandatory(),
      encoder.IntegerOption('gold-q', 0, 63).Mandatory(),
      encoder.IntegerOption('key-q', 0, 63).Mandatory(),
      encoder.ChoiceOption(['good', 'best', 'rt']),
    )
    # The start encoder is exactly the same as for VP8,
    # except that fixed-q, gold-q, alt-q and key-q parameters are set.
    # TODO(hta): Remove the options that have no effect in this mode.
    self.start_encoder_parameters = """ --lag-in-frames=0 \
      --kf-min-dist=3000 \
      --kf-max-dist=3000 --cpu-used=0 --static-thresh=0 \
      --token-parts=1 --drop-frame=0 --end-usage=cbr \
      --fixed-q=32 --gold-q=30 --alt-q=31 --key-q=28 \
      --undershoot-pct=100 --overshoot-pct=15 --buf-sz=1000 \
      --buf-initial-sz=800 --buf-optimal-sz=1000 --max-intra-rate=1200 \
      --resize-allowed=0 --passes=1 --best --noise-sensitivity=0 """

  def StartEncoder(self, context):
    return encoder.Encoder(context,
                           encoder.OptionValueSet(self.option_set,
                             self.start_encoder_parameters))

  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    # This is exactly the same as vp8.Execute, except that there is
    # no target-bitrate parameter.
    # TODO(hta): Redefine "parameters" so that the removal can be specified.
    commandline = (encoder.Tool('vpxenc-mpeg') + ' ' + parameters.ToString()
                   + ' --fps=' + str(videofile.framerate) + '/1'
                   + ' -w ' + str(videofile.width)
                   + ' -h ' + str(videofile.height)
                   + ' ' + videofile.filename
                   + ' --codec=vp8 '
                   + ' -o ' + encodedfile)
    return commandline

  def SpeedGroup(self, bitrate):
    """CQ encodings are independent of speed, so should not be grouped."""
    return 'all'

  def ConfigurationFixups(self, config):
    """Ensure that gold-q and key-q are smaller than fixed-q. """
    fixed_q_value = config.GetValue('fixed-q')
    if int(config.GetValue('gold-q')) > int(fixed_q_value):
      config = config.ChangeValue('gold-q', fixed_q_value)
    if int(config.GetValue('key-q')) > int(fixed_q_value):
      config = config.ChangeValue('key-q', fixed_q_value)

    return config

  def _SuggestTweakToName(self, encoding, name):
    """Returns a parameter string based on this encoding that has the
    parameter identified by "name" changed in a way worth testing.
    If no sensible change is found, returns None."""
    parameters = encoding.encoder.parameters
    value = int(parameters.GetValue(name))
    new_value = None
    if encoding.result['bitrate'] > encoding.bitrate:
      delta = 1
      new_value = 63
      candidates = range(value + 1, 64)
    else:
      delta = -1
      new_value = 0
      candidates = range(value - 1, -1, -1)
    # The range of Q values is from 0 to 63.
    if value + delta > 63:
      print name, 'maxed out at 63'
      return None # Already maxed out
    if value + delta < 0:
      print name, 'mined out at 0'
      return None # Already at bottom
    # If a previous result returned a score (which will be lower, since
    # the starting point is the highest score), try the middle value
    # between this and that. If none exists, go for the extreme values.
    for search_value in candidates:
      temp_params = parameters.ChangeValue(name, str(search_value))
      temp_params = self.ConfigurationFixups(temp_params)
      temp_encoder = encoder.Encoder(encoding.context, temp_params)
      temp_encoding = encoder.Encoding(temp_encoder, encoding.bitrate,
                                       encoding.videofile)
      temp_encoding.Recover()
      if temp_encoding.Result():
        print name, 'found scored value', search_value
        new_value = int((value + search_value) / 2)
        if new_value in (value, search_value):
          print name, 'already tried', value, '+1'
          return None # Already tried one-step-up
        break

    print name, "suggesting value", new_value
    parameters = parameters.ChangeValue(name, str(new_value))
    parameters = self.ConfigurationFixups(parameters)
    return parameters

  def SuggestTweak(self, encoding):
    """Suggest a tweak based on an encoding result.
    For fixed QP, suggest increasing min-q when bitrate is too high, otherwise
    suggest decreasing it.
    If a parameter is already at the limit, go to the next one."""
    if not encoding.result:
      return None

    parameters = self._SuggestTweakToName(encoding, 'fixed-q')
    if not parameters:
      parameters = self._SuggestTweakToName(encoding, 'gold-q')
    if not parameters:
      parameters = self._SuggestTweakToName(encoding, 'key-q')
    if not parameters:
      return None
    parameters = self.ConfigurationFixups(parameters)
    return encoder.Encoding(encoder.Encoder(encoding.context, parameters),
                    encoding.bitrate, encoding.videofile)
