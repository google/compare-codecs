"""VP8 codec definitions.

This constraint set operates in fixed QP mode.

It works by setting fixed-q, gold-q and key-q to given fixed values.
This requires a patch to the vpxenc binary.
"""
import os
import re
import subprocess

import encoder

import vp8


class Vp8CodecMpegMode(vp8.Vp8Codec):
  def __init__(self):
    super(Vp8CodecMpegMode, self).__init__()
    # Set the parts that are different from the VP8 codec.
    self.name = 'vp8-mpeg'
    self.options = [
      encoder.IntegerOption('fixed-q', 0, 63),
      encoder.IntegerOption('gold-q', 0, 63),
      encoder.IntegerOption('key-q', 0, 63),
      encoder.ChoiceOption(['good', 'best', 'rt']),
      ]
    # The start encoder is exactly the same as for VP8,
    # except that min-q and max-q have the same value.
    # TODO(hta): Remove the options that have no effect in this mode.
    self.start_encoder = encoder.Encoder(self, """ --lag-in-frames=0 \
      --kf-min-dist=3000 \
      --kf-max-dist=3000 --cpu-used=0 --static-thresh=0 \
      --token-parts=1 --drop-frame=0 --end-usage=cbr \
      --fixed-q=32 --gold-q=30 --alt-q=31 --key-q=28 \
      --undershoot-pct=100 --overshoot-pct=15 --buf-sz=1000 \
      --buf-initial-sz=800 --buf-optimal-sz=1000 --max-intra-rate=1200 \
      --resize-allowed=0 --passes=1 --best --noise-sensitivity=0 """)

  def Execute(self, parameters, bitrate, videofile, workdir):
    # This is exactly the same as vp8.Execute, except that there is
    # no target-bitrate parameter.
    # TODO(hta): Redefine "parameters" so that the removal can be specified.
    commandline = ("../bin/vpxenc-mpeg " + parameters
                   + ' --fps=' + str(videofile.framerate) + '/1'
                   + ' -w ' + str(videofile.width)
                   + ' -h ' + str(videofile.height)
                   + ' ' + videofile.filename
                   + ' --codec=vp8 '
                   + ' -o ' + workdir + '/' + videofile.basename + '.webm')
    print commandline
    with open('/dev/null', 'r') as nullinput:
      returncode = subprocess.call(commandline, shell=True, stdin=nullinput)
      if returncode:
        raise Exception("Encode failed with returncode " + str(returncode))
    return self.Measure(bitrate, videofile, workdir)

  def SpeedGroup(self, bitrate):
    """CQ encodings are independent of speed, so should not be grouped."""
    return 'all'

  def ConfigurationFixups(self, config):
    """Ensure that gold-q and key-q are smaller than fixed-q. """
    fixed_q_value = encoder.Option('fixed-q').GetValue(config)
    if encoder.Option('gold-q').GetValue(config) > fixed_q_value:
      config = encoder.Option('gold-q').SetValue(config, fixed_q_value)
    if encoder.Option('key-q').GetValue(config) > fixed_q_value:
      config = encoder.Option('key-q').SetValue(config, fixed_q_value)

    return config

  def _SuggestTweakToName(self, encoding, name):
    """Returns a parameter string based on this encoding that has the
    parameter identified by "name" changed in a way worth testing.
    If no sensible change is found, returns None."""
    parameters = encoding.encoder.parameters
    value = int(encoder.Option(name).GetValue(parameters))
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
      temp_params = encoder.Option(name).SetValue(parameters,
                                                  str(search_value))
      temp_params = self.ConfigurationFixups(temp_params)
      temp_encoder = encoder.Encoder(self, temp_params)
      temp_encoding = encoder.Encoding(temp_encoder, encoding.bitrate,
                                       encoding.videofile)
      temp_encoding.Recover()
      if temp_encoding.Score():
        print name, 'found scored value', search_value
        new_value = int((value + search_value) / 2)
        if new_value in (value, search_value):
          print name, 'already tried', value, '+1'
          return None # Already tried one-step-up
        break

    print name, "suggesting value", new_value
    parameters = encoder.Option(name).SetValue(parameters, str(new_value))
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
    return encoder.Encoding(encoder.Encoder(self, parameters),
                    encoding.bitrate, encoding.videofile)

