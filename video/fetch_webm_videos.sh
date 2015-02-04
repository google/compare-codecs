#!/bin/sh
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
# Fetch and decompress the videos for the comparison test.
#
set -e

files='
desktop_640_360_30.yuv
gipsrecmotion_1280_720_50.yuv
gipsrecstat_1280_720_50.yuv
kirland_640_480_30.yuv
macmarcomoving_640_480_30.yuv
macmarcostationary_640_480_30.yuv
niklas_1280_720_30.yuv
niklas_640_480_30.yuv
tacomanarrows_640_480_30.yuv
tacomasmallcameramovement_640_480_30.yuv
thaloundeskmtg_640_480_30.yuv
'

if which wget; then
  # Do nothing.
  true
else
  echo "No wget, exiting"
  exit 1
fi

for file in $files; do
  if [ ! -f $file ]; then
    # Remove earlier partial downloads.
    [ -f $file.xz ] && rm $file.xz
    wget http://downloads.webmproject.org/ietf_tests/$file.xz
    xz -d $file.xz
  else
    echo "Already have $file"
  fi
done
