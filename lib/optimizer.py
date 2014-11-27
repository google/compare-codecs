"""
Optimizer module.

An optimizer consists of:
- A codec
- A video file set, with associated target bitrates
- A set of scored encodings (the cache)
- A score function

It contains functions that allow to find and score encodings that will
perform highly on the score function.
"""

import encoder
import score_tools

class Optimizer(object):
  """Optimizer context for a codec.

  It is possible to ask an optimizer to find the best of something."""
  def __init__(self, codec, file_set=None,
               cache_class=None, score_function=None):
    self.context = encoder.Context(codec,
                                   cache_class or encoder.EncodingDiskCache)
    self.file_set = file_set
    self.score_function = score_function or score_tools.ScorePsnrBitrate

  def Score(self, encoding, scoredir=None):
    if scoredir is None:
      result = encoding.result
    else:
      result = encoding.encoder.context.cache.ReadEncodingResult(encoding,
          scoredir=scoredir)
    # Temporary hack because there are so many stored clips without cliptime
    # information:
    if encoding.result and not 'cliptime' in encoding.result:
      encoding.result['cliptime'] = encoding.videofile.ClipTime()
    return self.score_function(encoding.bitrate, result)

  def BestEncoding(self, bitrate, videofile):
    encodings = self.AllScoredEncodings(bitrate, videofile)
    if not encodings.Empty():
      return max(encodings.encodings, key=self.Score)
    else:
      return self.context.codec.StartEncoder(self.context).Encoding(bitrate,
                                                                    videofile)

  def AllScoredEncodings(self, bitrate, videofile):
    return self.context.cache.AllScoredEncodings(bitrate, videofile)



class FileAndRateSet(object):
  def __init__(self):
    pass

