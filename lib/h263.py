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
"""H.263 codec.
We use the H.263+ variant for its free scalability.
"""

import ffmpeg

class H263Codec(ffmpeg.FfmpegCodec):
  def __init__(self, name='h263'):
    super(H263Codec, self).__init__(name)
    self.codecname = 'h263p'
    self.extension = 'avi'
