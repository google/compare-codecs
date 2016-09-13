#!/usr/bin/python
# Copyright 2015 Google.
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
#

import encoder
import glob
import mpeg_settings
import optimizer
import os


class Error(Exception):
  pass


def ChooseRates(width, framerate):
  # pylint: disable=too-many-return-statements
  if width >= 1920 and framerate >= 50:
    return [3000, 4500, 7000, 10000]
  if width >= 1920 and framerate >= 24:
    return [1600, 2500, 4000, 6000]
  if width >= 1280 and framerate >= 60:
    return [384, 512, 850, 1500] # To match MPEG rates for Johnny
  if width >= 832 and framerate >= 50:
    return [512, 768, 1200, 2000]
  if width >= 416:
    return [384, 512, 850, 1500]
  if width >= 352:
    # CIF video. No standards activity is behind these chocies of rate.
    return [256, 384, 512, 850]
  if width >= 176:
    # QCIF video.
    return [256, 384, 512, 850, 1500]
  raise Error('Unhandled width/framerate combo: w=%d rate=%d' %
              (width, framerate))


def GenerateFilesetFromDirectory(name):
  """Returns a FileAndRateSet containing all the YUV files in the directory."""
  yuvfiles = glob.glob(os.path.join(os.getenv('WORKDIR'),
                                    'video', name, '*.yuv'))
  my_set = optimizer.FileAndRateSet()
  for yuvfile in yuvfiles:
    videofile = encoder.Videofile(yuvfile)
    my_set.AddFilesAndRates([videofile.filename],
                            ChooseRates(videofile.width, videofile.framerate))
  return my_set


def PickFileset(name):
  if name == 'mpeg_video':
    return mpeg_settings.MpegFiles()
  elif os.path.isdir(os.path.join('video', name)):
    return GenerateFilesetFromDirectory(name)
  else:
    raise Error('Fileset %s not found' % name)
