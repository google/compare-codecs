#!/usr/bin/python
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
"""A base class for all codecs using encode-to-file."""

import encoder
import filecmp
import json
import os
import re
import subprocess

class FileCodec(encoder.Codec):
  """Base class for file-using codecs.
  Subclasses MUST define:
  - EncodeCommandLine
  - DecodeCommandLine
  - ResultData
  """
  def __init__(self, name, formatter=None):
    super(FileCodec, self).__init__(name, formatter=formatter)
    self.extension = 'must-have-extension'

  def _EncodeFile(self, parameters, bitrate, videofile, encodedfile):
    commandline = self.EncodeCommandLine(
      parameters, bitrate, videofile, encodedfile)

    print commandline
    with open(os.path.devnull, 'r') as nullinput:
      times_start = os.times()
      returncode = subprocess.call(commandline, shell=True, stdin=nullinput)
      times_end = os.times()
      subprocess_cpu = times_end[2] - times_start[2]
      elapsed_clock = times_end[4] - times_start[4]
      print "Encode took %f CPU seconds %f clock seconds" % (
          subprocess_cpu, elapsed_clock)
      if returncode:
        raise Exception("Encode failed with returncode %d" % returncode)
      return (subprocess_cpu, elapsed_clock)

  def _DecodeFile(self, videofile, encodedfile, workdir):
    tempyuvfile = os.path.join(workdir,
                               videofile.basename + 'tempyuvfile.yuv')
    if os.path.isfile(tempyuvfile):
      print "Removing tempfile before decode:", tempyuvfile
      os.unlink(tempyuvfile)
    commandline = self.DecodeCommandLine(videofile, encodedfile, tempyuvfile)
    print commandline
    with open(os.path.devnull, 'r') as nullinput:
      subprocess_cpu_start = os.times()[2]
      returncode = subprocess.call(commandline, shell=True,
                                stdin=nullinput)
      if returncode:
        raise Exception('Decode failed with returncode %d' % returncode)
      subprocess_cpu = os.times()[2] - subprocess_cpu_start
      print "Decode took %f seconds" % subprocess_cpu
      commandline = encoder.Tool("psnr") + " %s %s %d %d 9999" % (
        videofile.filename, tempyuvfile, videofile.width,
        videofile.height)
      print commandline
      psnr = subprocess.check_output(commandline, shell=True, stdin=nullinput)
      commandline = ['md5sum', tempyuvfile]
      md5 = subprocess.check_output(commandline, shell=False)
      yuv_md5 = md5.split(' ')[0]
    os.unlink(tempyuvfile)
    return psnr, subprocess_cpu, yuv_md5

  def Execute(self, parameters, bitrate, videofile, workdir):
    encodedfile = os.path.join(workdir,
                               '%s.%s' % (videofile.basename, self.extension))
    subprocess_cpu, elapsed_clock = self._EncodeFile(parameters, bitrate,
                                                     videofile, encodedfile)
    result = {}

    result['encode_cputime'] = subprocess_cpu
    result['encode_clocktime'] = elapsed_clock
    result['encoder_version'] = self.EncoderVersion()
    bitrate = videofile.MeasuredBitrate(os.path.getsize(encodedfile))

    psnr, decode_cputime, yuv_md5 = self._DecodeFile(
        videofile, encodedfile, workdir)

    result['decode_cputime'] = decode_cputime
    result['yuv_md5'] = yuv_md5
    print "Bitrate", bitrate, "PSNR", psnr
    result['bitrate'] = int(bitrate)
    result['psnr'] = float(psnr)
    result['cliptime'] = videofile.ClipTime()
    result.update(self.ResultData(encodedfile))

    return result

  # Below are the fallback implementations of the interfaces
  # that the subclasses have to implement.
  def EncodeCommandLine(self, parameters, bitrate, videofile, encodedfile):
    """This function returns the command line that should be executed
    in order to turn an YUV file into an encoded file."""
    # pylint: disable=W0613,R0201
    raise encoder.Error('EncodeCommandLine not defined')

  def DecodeCommandLine(self, videofile, encodedfile, yuvfile):
    """This function returns the command line that should be executed
    in order to turn an encoded file into an YUV file."""
    # pylint: disable=W0613,R0201
    raise encoder.Error('DecodeCommandLine not defined')

  def ResultData(self, encodedfile):
    """Returns additional fields that the codec may know how to generate."""
    # pylint: disable=W0613,R0201
    return {}

  def VerifyEncode(self, parameters, bitrate, videofile, workdir):
    """Returns true if a new encode of the file gives exactly the same file."""
    old_encoded_file = '%s/%s.%s' % (workdir, videofile.basename,
                                     self.extension)
    if not os.path.isfile(old_encoded_file):
      raise encoder.Error('Old encoded file missing: %s' % old_encoded_file)
    new_encoded_file = '%s/%s_verify.%s' % (workdir, videofile.basename,
                                            self.extension)
    self._EncodeFile(parameters, bitrate, videofile,
                     new_encoded_file)
    if not VideoFilesEqual(old_encoded_file, new_encoded_file, self.extension):
      # If there is a difference, we leave the new encoded file so that
      # they can be compared by hand if desired.
      return False
    os.unlink(new_encoded_file)
    return True

  def EncoderVersion(self):
    raise encoder.Error('File codecs must define their own version')


# Tools that may be called upon by the codec implementation if needed.
def MatroskaFrameInfo(encodedfile):
  # Run the mkvinfo tool across the file to get frame size info.
  commandline = 'mkvinfo -v %s' % encodedfile
  print commandline
  mkvinfo = subprocess.check_output(commandline, shell=True)
  frameinfo = []
  for line in mkvinfo.splitlines():
    match = re.search(r'Frame with size (\d+)', line)
    if match:
      # The mkvinfo tool gives frame size in bytes. We want bits.
      frameinfo.append({'size': int(match.group(1))*8})

  return frameinfo


def FfmpegFrameInfo(encodedfile):
  # Uses the ffprobe tool to give frame info.
  commandline = '%s -loglevel warning -show_frames -of json %s' % (
      encoder.Tool('ffprobe'), encodedfile)
  ffprobeinfo = subprocess.check_output(commandline, shell=True)
  probeinfo = json.loads(ffprobeinfo)
  previous_position = 0
  frameinfo = []
  for frame in probeinfo['frames']:
    current_position = int(frame['pkt_pos'])
    if previous_position != 0:
      frameinfo.append({'size': 8 * (current_position - previous_position)})
    previous_position = current_position
  frameinfo.append({'size': 8 *
                    (os.path.getsize(encodedfile) - previous_position)})
  return frameinfo


def VideoFilesEqual(old_encoded_file, new_encoded_file, extension):
  if extension == 'webm':
    # Matroska files contain UIDs that vary even if the video content
    # is the same. So we must use vpxdec --md5 instead.
    old_checksum = subprocess.check_output((encoder.Tool('vpxdec'),
                                            '--md5',
                                            old_encoded_file))
    new_checksum = subprocess.check_output((encoder.Tool('vpxdec'),
                                            '--md5',
                                            new_encoded_file))
    return old_checksum == new_checksum
  else:
    return filecmp.cmp(old_encoded_file, new_encoded_file)
