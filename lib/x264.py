"""X264 codec definition.

This file defines how to run encode and decode for the x264 implementation
of H.264.
"""
import encoder
import file_codec

class X264Codec(file_codec.FileCodec):
  def __init__(self, name='x264'):
    super(X264Codec, self).__init__(name)
    self.extension = 'mkv'
    self.option_set = encoder.OptionSet(
    )

  def StartEncoder(self):
    return encoder.Encoder(self, encoder.OptionValueSet(self.option_set, ''))


  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    commandline = ('%(x264)s '
      '--vbv-maxrate %(bitrate)d --vbv-bufsize %(bitrate)d --vbv-init 0.8 '
      '--bitrate %(bitrate)d --fps %(framerate)d '
      '--threads 1 '
      '--rc-lookahead 0 '
      '--ref 2 '
      '--profile baseline --no-scenecut --keyint infinite --preset veryslow '
      '--input-res %(width)dx%(height)d '
      '--tune psnr '
      '-o %(outputfile)s %(inputfile)s') % {
      'x264': encoder.Tool('x264'),
      'bitrate': bitrate,
      'framerate': videofile.framerate,
      'width': videofile.width,
      'height': videofile.height,
      'outputfile': encodedfile,
      'inputfile': videofile.filename}
    return commandline


  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    commandline = '%s -i %s %s' % (encoder.Tool("ffmpeg"),
                                    encodedfile, yuvfile)
    return commandline

  def ResultData(self, encodedfile):
    more_results = {}
    more_results['frame'] = file_codec.MatroskaFrameInfo(encodedfile)
    return more_results

