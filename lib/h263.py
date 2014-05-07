"""H.263 codec.
We use the H.263+ variant for its free scalability.
"""

import ffmpeg

class H263Codec(ffmpeg.FfmpegCodec):
  def __init__(self, name='h263'):
    super(H263Codec, self).__init__(name)
    self.codecname = 'h263p'
    self.extension = 'avi'
