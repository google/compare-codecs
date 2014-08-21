"""X264 codec definition.

This file defines how to run encode and decode for the x264 implementation
of H.264.
"""
import os
import subprocess

import encoder

class X264Codec(encoder.Codec):
  def __init__(self, name='x264'):
    super(X264Codec, self).__init__(name)
    self.extension = 'mkv'
    self.options = [
      ]

  def StartEncoder(self):
    return encoder.Encoder(self, "")


  def Execute(self, parameters, bitrate, videofile, workdir):
    commandline = "%s \
      --vbv-maxrate %d --vbv-bufsize %d --vbv-init 0.8 \
      --bitrate %d --fps %d \
      --threads 1 \
      --rc-lookahead 0 \
      --ref 2 \
      --profile baseline --no-scenecut --keyint infinite --preset veryslow \
      --input-res %dx%d \
      --tune psnr \
      -o %s %s" % (
      encoder.Tool('x264'), bitrate, bitrate, bitrate,
      videofile.framerate, videofile.width, videofile.height,
      workdir + '/' + videofile.basename + self.extension,
      videofile.filename)
    print commandline
    with open('/dev/null', 'r') as nullinput:
      returncode = subprocess.call(commandline, shell=True, stdin=nullinput)
      if returncode:
        raise Exception("Encode failed with returncode %d" % returncode)
    return self.Measure(bitrate, videofile, workdir)

  def Measure(self, bitrate, videofile, workdir):
    result = {}
    tempyuvfile = "%s/%stempyuvfile.yuv" % (workdir, videofile.basename)
    if os.path.isfile(tempyuvfile):
      print "Removing tempfile before decode:", tempyuvfile
      os.unlink(tempyuvfile)
    commandline = "%s -i %s/%s.%s %s" % (
      encoder.Tool('ffmpeg'),
      workdir, videofile.basename, self.extension, tempyuvfile)
    print commandline
    returncode = subprocess.call(commandline, shell=True)
    if returncode:
      raise encoder.Error('Decode failed')

    bitrate = videofile.MeasuredBitrate(
      os.path.getsize('%s/%s.%s' % (workdir, videofile.basename,
                                    self.extension)))
    commandline = "%s %s %s %d %d 9999" % (
      encoder.Tool('psnr'),
      videofile.filename, tempyuvfile, videofile.width,
      videofile.height)
    print commandline
    psnr = subprocess.check_output(commandline, shell=True)
    print "Bitrate", bitrate, "PSNR", psnr
    result['bitrate'] = int(bitrate)
    result['psnr'] = float(psnr)
    os.unlink(tempyuvfile)
    return result

  def ScoreResult(self, target_bitrate, result):
    if not result:
      return None
    score = result['psnr']
    if result['bitrate'] > int(target_bitrate):
      score -= (result['bitrate'] - int(target_bitrate)) * 0.1
      if abs(score) < 0.01:
        score = 0.01
    return score
