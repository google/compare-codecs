# Copyright 2015 Google.
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
"""An encoder using the libavc encoder from Android M."""
import encoder
import file_codec
import subprocess

class LibavcCodec(file_codec.FileCodec):

  def __init__(self,
      name='libavc',
      formatter=None):
    self.name = name
    self.codecname = 'libavc'
    super(LibavcCodec, self).__init__(
        name,
        formatter=(formatter or
                   encoder.OptionFormatter(prefix='--', infix=' ')))
    self.extension = 'avi'
    self.option_set = encoder.OptionSet(
        # Rate control. 0 = constant QP, 1 = storage, 2 = CBR high delay,
        # 3 = CBR low delay
        # 2 and 3 seems to drop frames - sometimes, but not always.
        # 3 is able to run out of memory.
        encoder.Option('rc', ['0', '1']),
    )

  def StartEncoder(self, context):
    return encoder.Encoder(context, encoder.OptionValueSet(self.option_set, ''))

  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    commandline = (
        '%(tool)s '
        '--width %(width)d --height %(height)d '
        '--src_framerate %(framerate)d --tgt_framerate %(framerate)d '
        '--input_chroma_format YUV_420P --bitrate %(bitrate)d '
        '%(parameters)s '
        '--input %(inputfile)s --output %(outputfile)s' % {
            'tool': encoder.Tool('avcenc'),
            'width': videofile.width,
            'height': videofile.height,
            'framerate': videofile.framerate,
            'bitrate': bitrate * 1000, # Bitrate is in bits/sec, not kilobits.
            'parameters': parameters.ToString(),
            'inputfile': videofile.filename,
            'outputfile': encodedfile}
    )
    return commandline

  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    commandline = "%s -loglevel warning -codec:v h264 -i %s %s" % (
        encoder.Tool('ffmpeg'),
        encodedfile, yuvfile)
    return commandline

  def ResultData(self, encodedfile):
    return {'frame': file_codec.FfmpegFrameInfo(encodedfile)}

  def EncoderVersion(self):
    # libavc doesn't appear to have a built-in version string. Use the
    # git checksum instead.
    git_hash = subprocess.check_output(
        'cd third_party/libavc; git log --format="%h %ad" -1', shell=True)
    return 'libavc %s' % git_hash
