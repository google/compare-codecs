# Copyright 2014 Google.
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
"""A codec picker."""

import encoder
import h261
import h263
import hevc_jm
import mjpeg
import vp8
import vp8_mpeg
import vp8_mpeg_1d
import vp9
import ffmpeg
import x264
import x264_baseline
import x264_realtime
import x265

class CodecInfo(object):
  def __init__(self, constructor, shortname, longname):
    self.constructor = constructor
    self.shortname = shortname
    self.longname = longname

codec_map = {
  'vp8': CodecInfo(vp8.Vp8Codec, 'VP8', 'VP8'),
  'vp8_mpeg' : CodecInfo(vp8_mpeg.Vp8CodecMpegMode, 'VP8MP',
                         'VP8 in MPEG-compatible mode'),
  'vp8_mpeg_1d' : CodecInfo(vp8_mpeg_1d.Vp8CodecMpeg1dMode, 'VP8M1',
                            'VP8 in 1-variable MPEG mode'),
  'vp9': CodecInfo(vp9.Vp9Codec, 'VP9', 'VP9'),
  'ffmpeg' : CodecInfo(ffmpeg.FfmpegCodec, 'FFMPEG', 'FFMPEG'),
  'mjpeg' : CodecInfo(mjpeg.MotionJpegCodec, 'MJPEG', 'Motion JPEG'),
  'h261': CodecInfo(h261.H261Codec, 'H261', 'H.261'),
  'h263': CodecInfo(h263.H263Codec, 'H263', 'H.263'),
  'x264': CodecInfo(x264.X264Codec, 'H264', 'H.264 - x264 implementation'),
  'x264_base': CodecInfo(x264_baseline.X264BaselineCodec, 'H264-BL',
                         'H264 Baseline - x264 implementation'),
  'x264_rt': CodecInfo(x264_realtime.X264RealtimeCodec, 'H264-RT',
                       'H264 - x264 implementation, realtime settings'),
  'x265': CodecInfo(x265.X265Codec, 'H265', 'HEVC - x265 implementation'),
  'hevc': CodecInfo(hevc_jm.HevcCodec, 'HEVC', 'HEVC - JM implementation'),
}


def PickCodec(name):
  if name is None:
    name = 'vp8'
  if name in codec_map:
    return codec_map[name].constructor()
  raise encoder.Error('Unrecognized codec name %s' % name)


def ShortName(name):
  """Return a pretty but short name for the codec."""
  if name in codec_map:
    return codec_map[name].shortname
  raise encoder.Error('Unrecognized codec name %s' % name)

def LongName(name):
  """Return a pretty but long name for the codec."""
  if name in codec_map:
    return codec_map[name].longname
  raise encoder.Error('Unrecognized codec name %s' % name)
