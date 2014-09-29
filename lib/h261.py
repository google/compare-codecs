"""H.261 codec.

This uses ffmpeg for encoding and decoding.
"""
import encoder
import ffmpeg

class H261Codec(ffmpeg.FfmpegCodec):
  def __init__(self, name='h261'):
    super(H261Codec, self).__init__(name)
    self.codecname = 'h261'
    self.extension = 'h261'

  def StartEncoder(self):
    return encoder.Encoder(self, encoder.OptionValueSet(self.option_set, ''))

  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    # TODO(hta): Merge the common parts of this with vp8.Execute.
    commandline = (
      '%s %s -s %dx%d -i %s -codec:v %s -b:v %dk -y -s 352x288 %s' % (
        encoder.Tool('ffmpeg'),
        parameters.ToString(), videofile.width, videofile.height,
        videofile.filename, self.codecname,
        bitrate, encodedfile))
    return commandline

  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    # The special thing here is that it rescales back to the original size.
    commandline = "%s -i %s -s %sx%s %s" % (
      encoder.Tool('ffmpeg'),
      encodedfile, videofile.width, videofile.height,
      yuvfile)
    return commandline

