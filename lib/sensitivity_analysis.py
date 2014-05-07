#!/usr/bin/python
#
# Analyze the sensitivity of a set of encodings to their variable parameters.
#
import argparse
import sys

import encoder
import mpeg_settings
import pick_codec

def AnalyzeVariants(encoding, score=False):
  codec = encoding.encoder.codec
  for option in codec.options:
    # Get sensitivity on integer-valued options.
    param_here = encoding.encoder.parameters
    try:
      value = int(option.GetValue(param_here))
    except ValueError:
      continue
    # Hackish!
    if value > option.min:
      param_low = option.SetValue(param_here, str(value-1))
      encoding_low = encoder.Encoding(encoder.Encoder(codec, param_low),
                                      encoding.bitrate, encoding.videofile)
      encoding_low.Recover()
      if score and not encoding_low.Score():
        encoding_low.Execute()
        encoding_low.Store()
      if encoding_low.Score():
        print option.name, value, '-1', encoding_low.result,
        print encoding_low.result['bitrate'] - encoding.result['bitrate'],
        print encoding_low.result['psnr'] - encoding.result['psnr']
    else:
      print option.name, value, 'at lower limit'

    if value < option.max:
      param_high = option.SetValue(param_here, str(value+1))
      encoding_high = encoder.Encoding(encoder.Encoder(codec, param_high),
                                       encoding.bitrate, encoding.videofile)
      encoding_high.Recover()
      if score and not encoding_high.Score():
        encoding_high.Execute()
        encoding_high.Store()
      if encoding_high.Score():
        print option.name, value, '+1', encoding_high.result,
        print -encoding_high.result['bitrate'] + encoding.result['bitrate'],
        print -encoding_high.result['psnr'] + encoding.result['psnr']
    else:
      print option.name, value, 'at upper limit'

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--codec')
  parser.add_argument('--score', action='store_true', default=False)
  args = parser.parse_args()

  codec = pick_codec.PickCodec(args.codec)
  for classname in mpeg_settings.files.keys():
    for file in mpeg_settings.files[classname]:
      for rate in mpeg_settings.rates[classname]:
        videofile = encoder.Videofile('../mpeg_video/%s' % file)
        encoding = codec.BestEncoding(rate, videofile)
        print rate, file, encoding.Score(), encoding.result
        AnalyzeVariants(encoding, args.score)
  return 0

if __name__ == '__main__':
  sys.exit(main())
