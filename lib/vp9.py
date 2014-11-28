"""VP9 codec definitions.

This is an instance of a codec definition.
It tells the generic codec the following:
- Name of codec = directory of codec database
- File extension
- Options table
"""
import encoder
import file_codec

class Vp9Codec(file_codec.FileCodec):
  def __init__(self, name='vp9'):
    super(Vp9Codec, self).__init__(name)
    self.extension = 'webm'
    self.option_set = encoder.OptionSet(
      encoder.IntegerOption('cpu-used', 0, 16),
      encoder.ChoiceOption(['good', 'best', 'rt']),
    )

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(self.option_set,
        '--passes=1 --good --noise-sensitivity=0 --cpu-used=5'))

  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    commandline = (encoder.Tool('vpxenc') + ' ' + parameters.ToString()
                   + ' --target-bitrate=' + str(bitrate)
                   + ' --fps=' + str(videofile.framerate) + '/1'
                   + ' -w ' + str(videofile.width)
                   + ' -h ' + str(videofile.height)
                   + ' ' + videofile.filename
                   + ' --codec=vp9 '
                   + ' -o ' + encodedfile)
    return commandline

  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    commandline = '%s %s --i420 -o %s' % (encoder.Tool("vpxdec"),
                                    encodedfile, yuvfile)
    return commandline

  def ResultData(self, encodedfile):
    more_results = {}
    more_results['frame'] = file_codec.MatroskaFrameInfo(encodedfile)
    return more_results
