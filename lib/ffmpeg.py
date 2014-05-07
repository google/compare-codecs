"""Framework for specifying encoders from ffmpeg.

This uses ffmpeg for encoding and decoding.
The default FFMPEG encoder uses mpeg4, so that we can see if it's roughly
compatible with the vpxenc-produced qualities.
"""
import os
import re
import subprocess

import encoder

class FfmpegCodec(encoder.Codec):
  def __init__(self, name='ffmpeg-mpeg4'):
    # Subclasses need to override name, codecname and extension.
    # At the moment, no parameters are defined.
    self.name = name
    self.codecname = 'mpeg4'
    self.extension = 'avi'
    super(FfmpegCodec, self).__init__(name)
    self.options = [
      ]
    self.start_encoder = encoder.Encoder(self, '')

  def Execute(self, parameters, bitrate, videofile, workdir):
    commandline = (
      '../bin/ffmpeg %s -s %dx%d -i %s -codec:v %s -b:v %dk -y %s/%s.%s' % (
        parameters, videofile.width, videofile.height,
        videofile.filename, self.codecname,
        bitrate, workdir, videofile.basename, self.extension))
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
    commandline = "../bin/ffmpeg -codec:v %s -i %s/%s.%s %s" % (
      self.codecname,
      workdir, videofile.basename, self.extension, tempyuvfile)
    print commandline
    returncode = subprocess.call(commandline, shell=True)
    if returncode:
      raise encoder.Error('Decode failed')
    bitrate = videofile.MeasuredBitrate(
      os.path.getsize('%s/%s.%s' % (workdir, videofile.basename,
                                    self.extension)))
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

  def ScoreResult(self, target_bitrate, result):
    if not result:
      return None
    score = result['psnr']
    if result['bitrate'] > int(target_bitrate):
      score -= (result['bitrate'] - int(target_bitrate)) * 0.1
      if abs(score) < 0.01:
        score = 0.01
    return score

