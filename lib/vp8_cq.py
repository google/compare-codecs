"""VP8 codec definitions.

This constraint set operates in fixed QP mode.

It works by picking min-q and forcing max-q to the same value.
"""
import os
import re
import subprocess

import encoder
import vp8

class Vp8CodecCqMode(vp8.Vp8Codec):
  def __init__(self):
    super(Vp8CodecCqMode, self).__init__('vp8-cq')
    # Set the parts that are different from the VP8 codec.
    self.options = [
      encoder.IntegerOption('min-q', 0, 63),
      encoder.ChoiceOption(['good', 'best', 'rt']),
      ]
    # The start encoder is exactly the same as for VP8,
    # except that min-q and max-q have the same value.
    # TODO(hta): Remove the options that have no effect in this mode.
    self.start_encoder = encoder.Encoder(self, """ --lag-in-frames=0 \
      --kf-min-dist=3000 \
      --kf-max-dist=3000 --cpu-used=0 --static-thresh=0 \
      --token-parts=1 --drop-frame=0 --end-usage=cbr --min-q=32 --max-q=32 \
      --undershoot-pct=100 --overshoot-pct=15 --buf-sz=1000 \
      --buf-initial-sz=800 --buf-optimal-sz=1000 --max-intra-rate=1200 \
      --resize-allowed=0 --passes=1 --best --noise-sensitivity=0 """)

  def Execute(self, parameters, bitrate, videofile, workdir):
    # This is exactly the same as vp8.Execute, except that there is
    # no target-bitrate parameter.
    commandline = ("../bin/vpxenc " + parameters
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
    """Ensure fixed CQ by setting min-q and max-q to the same value."""
    return encoder.Option('max-q').SetValue(
      config, encoder.Option('min-q').GetValue(config))

  def SuggestTweak(self, encoding):
    """Suggest a tweak based on an encoding result.
    For fixed QP, suggest increasing min-q when bitrate is too high, otherwise
    suggest decreasing it."""
    if not encoding.result:
      return None
    if encoding.result['bitrate'] > encoding.bitrate:
      delta = 1
    else:
      delta = -1
    parameters = encoding.encoder.parameters
    value = int(encoder.Option('min-q').GetValue(parameters))
    # The range of min-q is from 0 to 63.
    if value + delta > 63:
      return None # Already maxed out
    if value + delta < 0:
      return None # Already at bottom
    new_value = value + delta
    parameters = encoder.Option('min-q').SetValue(parameters, str(new_value))
    parameters = self.ConfigurationFixups(parameters)
    return encoder.Encoding(encoder.Encoder(self, parameters),
                    encoding.bitrate, encoding.videofile)

