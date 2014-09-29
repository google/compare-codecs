"""VP8 codec definitions.

This constraint set operates in fixed QP mode, with a fixed relationship
between fixed-q, gold-q and key-q.

It exists for easily generating consistent sets for MPEG tests.
"""
import encoder

import vp8_mpeg


class Vp8CodecMpeg1dMode(vp8_mpeg.Vp8CodecMpegMode):
  def __init__(self, name='vp8-mp1'):
    super(Vp8CodecMpeg1dMode, self).__init__(name)
    # Set the parts that are different from the VP8 MPEG codec.
    self.option_set = encoder.OptionSet(
      encoder.IntegerOption('key-q', 0, 63),
      encoder.DummyOption('fixed-q'),
      encoder.DummyOption('gold-q'),
    )

  def ConfigurationFixups(self, config):
    """Ensure that gold-q and key-q are set from fixed-q. """
    key_q_value = config.GetValue('key-q')
    fixed_q = float(key_q_value) * 2.0
    gold_q = float(fixed_q) / 1.5
    if fixed_q > 63:
      fixed_q = 63
    if gold_q > 63:
      gold_q = 63
    config = config.ChangeValue('gold-q', str(int(gold_q)))
    config = config.ChangeValue('fixed-q', str(int(fixed_q)))
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

