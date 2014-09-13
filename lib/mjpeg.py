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
    self.start_encoder = encoder.Encoder(self, '')
