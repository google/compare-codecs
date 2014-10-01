"""Motion JPEG codec.

This uses ffmpeg for encoding and decoding.
"""
import encoder
import ffmpeg

class MotionJpegCodec(ffmpeg.FfmpegCodec):
  def __init__(self, name='mjpeg'):
    super(MotionJpegCodec, self).__init__(name)
    self.codecname = 'mjpeg'
    self.extension = 'mjpeg'
    self.option_set = encoder.OptionSet(
      encoder.IntegerOption('qmin', 0, 1),
      encoder.IntegerOption('qmax', 0, 1),
    )
    self.option_formatter = encoder.OptionFormatter(prefix='-', infix=' ')

  def StartEncoder(self):
    return encoder.Encoder(
      self, encoder.OptionValueSet(self.option_set, '',
                                   formatter=self.option_formatter))

