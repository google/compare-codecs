"""VP8 codec definitions.

This constraint set operates in fixed QP mode, with a fixed relationship
between fixed-q, gold-q and key-q.

It exists for easily generating consistent sets for MPEG tests.
"""
import os
import re
import subprocess

import encoder

import vp8_mpeg


class Vp8CodecMpeg1dMode(vp8_mpeg.Vp8CodecMpegMode):
  def __init__(self):
    super(Vp8CodecMpeg1dMode, self).__init__()
    # Set the parts that are different from the VP8 codec.
    self.name = 'vp8-mp1'
    self.options = [
      encoder.IntegerOption('key-q', 0, 63),
      ]
    self.start_encoder = encoder.Encoder(self,
      self.ConfigurationFixups(self.start_encoder.parameters))

  def ConfigurationFixups(self, config):
    """Ensure that gold-q and key-q are set from fixed-q. """
    key_q_value = encoder.Option('key-q').GetValue(config)
    fixed_q = float(key_q_value) * 2.0
    gold_q = float(fixed_q) / 1.5
    if fixed_q > 63:
      fixed_q = 63
    if gold_q > 63:
      gold_q = 63
    config = encoder.Option('gold-q').SetValue(config, str(int(gold_q)))
    config = encoder.Option('fixed-q').SetValue(config, str(int(fixed_q)))
    return config

  def SuggestTweak(self, encoding):
    """Suggest a tweak based on an encoding result.
    For fixed QP, suggest increasing min-q when bitrate is too high, otherwise
    suggest decreasing it.
    If a parameter is already at the limit, go to the next one."""
    if not encoding.result:
      return None

    parameters = self._SuggestTweakToName(encoding, 'key-q')
    if parameters:
      return encoder.Encoding(encoder.Encoder(self, parameters),
                              encoding.bitrate, encoding.videofile)
    return None

