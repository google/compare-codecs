"""VP8 codec definitions.

This is an instance of a codec definition.
It tells the generic codec the following:
- Name of codec = directory of codec database
- File extension
- Options table
"""
import os
import subprocess

import encoder

class Vp8Codec(encoder.Codec):
  def __init__(self, name='vp8'):
    super(Vp8Codec, self).__init__(name)
    self.extension = 'webm'
    self.options = [
      encoder.Option('overshoot-pct', ['0', '15', '30', '45']),
      encoder.Option('undershoot-pct', ['0', '25', '50', '75', '100']),
      # CQ mode is not considered for end-usage at the moment.
      encoder.Option('end-usage', ['cbr', 'vbr']),
      # End-usage cq doesn't really make sense unless we also set q to something
      # between min and max. This is being checked.
      # encoder.Option('end-usage', ['cbr', 'vbr', 'cq']),
      encoder.Option('end-usage', ['cbr', 'vbr']),
      encoder.Option('min-q', ['0', '2', '4', '8', '16', '24']),
      encoder.Option('max-q', ['32', '56', '63']),
      encoder.Option('buf-sz', ['200', '500', '1000', '2000', '4000', '8000', '16000']),
      encoder.Option('buf-initial-sz', ['200', '400', '800', '1000', '2000', '4000', '8000', '16000']),
      encoder.Option('max-intra-rate', ['100', '200', '400', '600', '800', '1200']),
      encoder.ChoiceOption(['good', 'best', 'rt']),
      ]
    self.start_encoder = encoder.Encoder(self, """ --lag-in-frames=0 \
      --kf-min-dist=3000 \
      --kf-max-dist=3000 --cpu-used=0 --static-thresh=0 \
      --token-parts=1 --drop-frame=0 --end-usage=cbr --min-q=2 --max-q=56 \
      --undershoot-pct=100 --overshoot-pct=15 --buf-sz=1000 \
      --buf-initial-sz=800 --buf-optimal-sz=1000 --max-intra-rate=1200 \
      --resize-allowed=0 --drop-frame=0 --passes=1 --good --noise-sensitivity=0 """)

  def Execute(self, parameters, bitrate, videofile, workdir):
    nullinput = open('/dev/null', 'r')
    commandline = ("../bin/vpxenc " + parameters
                   + ' --target-bitrate=' + str(bitrate)
                   + ' --fps=' + str(videofile.framerate) + '/1'
                   + ' -w ' + str(videofile.width)
                   + ' -h ' + str(videofile.height)
                   + ' ' + videofile.filename
                   + ' --codec=vp8 '
                   + ' -o ' + workdir + '/' + videofile.basename + '.webm')
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
    commandline = "../bin/ffmpeg -i %s/%s.webm %s 2>&1 | awk '/bitrate:/ { print $6 }'" % (workdir, videofile.basename,
                         tempyuvfile)
    print commandline
    with open('/dev/null', 'r') as nullinput:
      bitrate = subprocess.check_output(commandline, shell=True, stdin=nullinput)
      commandline = "../bin/psnr %s %s %d %d 9999" % (
        videofile.filename, tempyuvfile, videofile.width,
        videofile.height)
      print commandline
      psnr = subprocess.check_output(commandline, shell=True, stdin=nullinput)
    print "Bitrate", bitrate, "PSNR", psnr
    result['bitrate'] = int(bitrate)
    result['psnr'] = float(psnr)
    os.unlink(tempyuvfile)
    return result

  def ScoreResult(self, target_bitrate, result):
    if not result:
      return None
    score = result['psnr']
    # Check that target_bitrate is an integer.
    assert(type(target_bitrate) == type(0))
    if result['bitrate'] > target_bitrate:
      score -= (result['bitrate'] - target_bitrate) * 0.1
      # Avoid accidentally-false scores.
      if abs(score) < 0.01:
        score = 0.01
    return score
