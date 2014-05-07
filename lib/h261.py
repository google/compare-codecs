"""H.261 codec.

This uses ffmpeg for encoding and decoding.
"""
import os
import re
import subprocess

import encoder
import ffmpeg

class H261Codec(ffmpeg.FfmpegCodec):
  def __init__(self, name='h261'):
    super(H261Codec, self).__init__(name)
    self.codecname = 'h261'
    self.extension = 'h261'
    self.start_encoder = encoder.Encoder(self, """\
 """)

  def Execute(self, parameters, bitrate, videofile, workdir):
    # TODO(hta): Merge the common parts of this with vp8.Execute.
    commandline = (
      '../bin/ffmpeg %s -s %dx%d -i %s -codec:v %s -b:v %dk -y -s 352x288 %s/%s.%s' % (
        parameters, videofile.width, videofile.height,
        videofile.filename, self.codecname,
        str(bitrate), workdir, videofile.basename, self.extension))

    print commandline
    returncode = subprocess.call(commandline, shell=True)
    if returncode:
      raise Exception("Encode failed with returncode " + str(returncode))
    return self.Measure(bitrate, videofile, workdir)

  def Measure(self, bitrate, videofile, workdir):
    result = {}
    tempyuvfile = "%s/%stempyuvfile.yuv" % (workdir, videofile.basename)
    if os.path.isfile(tempyuvfile):
      print "Removing tempfile before decode:", tempyuvfile
      os.unlink(tempyuvfile)
    # The special thing here is that it rescales back to the original size.
    # TODO(hta): Factor out the difference by itself.
    commandline = "../bin/ffmpeg -i %s/%s.h261 -s %sx%s %s" % (
      workdir, videofile.basename, videofile.width, videofile.height,
      tempyuvfile)
    print commandline
    returncode = subprocess.call(commandline, shell=True)
    if returncode:
      raise encoder.Error('Decode failed')
    bitrate = videofile.MeasuredBitrate(
      os.path.getsize('%s/%s.h261' % (workdir, videofile.basename)))
    commandline = "../bin/psnr %s %s %d %d 9999" % (
                         videofile.filename, tempyuvfile, videofile.width,
                         videofile.height)
    print commandline
    psnr = subprocess.check_output(commandline, shell=True)
    print "Bitrate", bitrate, "PSNR", psnr
    result['bitrate'] = int(bitrate)
    result['psnr'] = float(psnr)
    os.unlink(tempyuvfile)
    return result

