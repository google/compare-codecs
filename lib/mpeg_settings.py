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
#

import optimizer

# Files and rates for the MPEG 2nd CFP for RF codecs, early 2013.
def OldMpegFiles():
  the_set = optimizer.FileAndRateSet()
  my_directory = 'video/mpeg_video'
  # Class A
  the_set.AddFilesAndRates(["Traffic_2560x1600_30_crop.yuv",
                            "PeopleOnStreet_2560x1600_30_crop.yuv"],
                           [2500, 3500, 5000, 8000, 14000],
                           my_directory)
  # Class B1
  the_set.AddFilesAndRates(["Kimono1_1920x1080_24.yuv",
                            "ParkScene_1920x1080_24.yuv"],
                           [1000, 1600, 2500, 4000, 6000],
                           my_directory)
  # Class B2
  the_set.AddFilesAndRates(["Cactus_1920x1080_50.yuv",
                            "BasketballDrive_1920x1080_50.yuv"],
                           [2000, 3000, 4500, 7000, 10000],
                            my_directory)
  # Class C
  the_set.AddFilesAndRates(["BasketballDrill_832x480_50.yuv",
                            "BQMall_832x480_60.yuv",
                            "PartyScene_832x480_50.yuv",
                            "RaceHorses_832x480_30.yuv"],
                           [384, 512, 768, 1200, 2000],
                            my_directory)
  # Class D
  the_set.AddFilesAndRates(["BasketballPass_416x240_50.yuv",
                            "BlowingBubbles_416x240_50.yuv",
                            "RaceHorses_416x240_30.yuv"],
                           [256, 384, 512, 850, 1500],
                            my_directory)
  # Class E
  the_set.AddFilesAndRates(["FourPeople_1280x720_60.yuv",
                            "Johnny_1280x720_60.yuv",
                            "KristenAndSara_1280x720_60.yuv"],
                           [256, 384, 512, 850, 1500],
                            my_directory)
  return the_set


# Files and rates for the MPEG codec comparison test, December 2013.
def MpegFiles():
  the_set = optimizer.FileAndRateSet()
  my_directory = 'video/mpeg_video'
  # Class A
  the_set.AddFilesAndRates(["Kimono1_1920x1080_24.yuv",
                            "ParkScene_1920x1080_24.yuv"],
                           [1600, 2500, 4000, 6000],
                           my_directory)
  # Class B
  the_set.AddFilesAndRates(["Cactus_1920x1080_50.yuv",
                            "BasketballDrive_1920x1080_50.yuv"],
                           [3000, 4500, 7000, 10000],
                            my_directory)
  # Class C
  the_set.AddFilesAndRates(["BasketballDrill_832x480_50.yuv",
                            "BQMall_832x480_60.yuv",
                            "PartyScene_832x480_50.yuv",
                            "RaceHorses_832x480_30.yuv"],
                           [512, 768, 1200, 2000],
                            my_directory)
  # Class D
  the_set.AddFilesAndRates(["FourPeople_1280x720_60.yuv",
                            "Johnny_1280x720_60.yuv",
                            "KristenAndSara_1280x720_60.yuv"],
                           [384, 512, 850, 1500],
                            my_directory)
  return the_set
