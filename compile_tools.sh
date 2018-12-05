#!/bin/bash
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
# Compile and install required software tools to run the tests.
#
# This script has been tested on Ubuntu, Trusty Tahr.
#
set -e

if [ -z "$WORKDIR" -o ! -d "$WORKDIR" ]; then
  echo "Workdir not set correctly: $WORKDIR"
  echo "Did you run init.sh?"
  exit 1
fi

TOOLDIR=$CODEC_TOOLPATH
if [ -z "$TOOLDIR" -o ! -d "$TOOLDIR" ]; then
  echo Tooldir not set correctly: $TOOLDIR
  echo "Did you run init.sh?"
  exit 1
fi

echo "Compiling into $TOOLDIR"

cd $WORKDIR

# Build the psnr binary.
echo "Compiling psnr"
gcc -o $TOOLDIR/psnr src/psnr.c -lm

# Build third party source
cd $WORKDIR/third_party

# The program continues after the function declarations.

build_vpxenc() {
  # Build the vpxenc and vpxdec binaries
  if [ ! -d libvpx ]; then
    git clone https://chromium.googlesource.com/webm/libvpx
  fi
  cd libvpx
  # Ensure we check out exactly a consistent version.
  git checkout -f master
  #git checkout v1.3.0
  # Check out the Oct 20 2014 version of libvpx.
  # git checkout 9c98fb2bab6125a0614576bf7635981163b1cc79
  git checkout v1.6.0
  ./configure
  # Leftovers from previous compilations may be troublesome.
  make clean
  make
  cp vpxenc $TOOLDIR
  cp vpxdec $TOOLDIR

  # Build a patched version of vpxenc that supports setting
  # the q-value for key-frames, golden frames and alt-frames separately
  # from the generic fixed q value that is used for all other frames.
  patch -p1 < ../vp8_fixed_q.patch
  make
  cp vpxenc $TOOLDIR/vpxenc-mpeg
}

build_x264() {
  # Build the x264 binary.
  if [ ! -d x264 ]; then
    git clone git://git.videolan.org/x264.git
  fi
  cd x264
  # This version of x264 is chosen because the next step requires yasm 1.2.
  # Was: git checkout d967c09
  # git checkout 8a9608
  # Latest version as of Oct 20 2014 - version above crashes on trusty.
  git checkout dd79a61

  ./configure
  make x264
  cp x264 $TOOLDIR
}

build_ffmpeg() {
  # Build the ffmpeg binary.
  if [ ! -d ffmpeg ]; then
    git clone git://source.ffmpeg.org/ffmpeg.git ffmpeg
  fi
  cd ffmpeg
  # A known working 2012 version (without H265 support)
  # git checkout ae04493
  # A Feb 2015 version
  # git checkout 60bb893
  # Checking out a named version.
  git fetch origin release/2.4
  git checkout n2.4.3
  ./configure
  make clean
  make ffmpeg
  cp ffmpeg $TOOLDIR
  make ffprobe
  cp ffprobe $TOOLDIR
}

build_x265() {
  # Build the x265 binary.
  if [ ! -d x265 ]; then
    hg clone https://bitbucket.org/multicoreware/x265
  fi
  cd x265/build/linux
  hg update 1.5
  rm -f CMakeCache.txt
  cmake ../../source
  make
  cp x265 $TOOLDIR
}

build_hevc_hm() {

  # Build the HEVC HM
  if [ ! -d jctvc-hm ]; then
    mkdir jctvc-hm
  fi
  HM_VERSION=HM-16.3
  cd jctvc-hm
  svn checkout svn://hevc.kw.bbc.co.uk/svn/jctvc-hm/tags/$HM_VERSION
  pushd $HM_VERSION/build/linux
  make
  popd
  cp $HM_VERSION/bin/TAppDecoderStatic $TOOLDIR
  cp $HM_VERSION/bin/TAppEncoderStatic $TOOLDIR
  # Encoding with HM is impossible without config files.
  cp $HM_VERSION/cfg/encoder_randomaccess_main.cfg $TOOLDIR/hevc_ra_main.cfg
}

build_openh264() {
  # Build the Open H264 implementation.
  if [ ! -d openh264 ]; then
    git clone git@github.com:cisco/openh264.git
  fi
  cd openh264
  git fetch --tags
  # 7e3c064 is the version that enables the -frin option which will be used in scripts
  # This was referenced per April 2015, but is gone from the repo
  # as of Aug 9, 2016.
  # git checkout 7e3c064
  # Version 1.5.0 is from October 2015.
  git checkout v1.5.0
  make
  cp h264enc $TOOLDIR
  cp h264dec $TOOLDIR
  cp testbin/welsenc.cfg $TOOLDIR/openh264.cfg
  cp testbin/layer2.cfg $TOOLDIR/layer2.cfg
}

build_libavc() {
  # Build the Android M libavc
  if [ ! -d libavc ]; then
    git clone https://android.googlesource.com/platform/external/libavc
  fi
  (cd libavc; git fetch --tags)
  (cd libavc; git checkout android-6.0.1_r63)
  (cd libavc; make -f ../../src/Makefile.libavcenclib)
  (cd libavc/test; make -f ../../../src/Makefile.libavcencoder)
  cp libavc/test/avcenc $TOOLDIR/avcenc
}

# Selecting which components to build.
build_func () {
while [ "$1" != "" ]; do
  cd $WORKDIR/third_party
  case $1 in
    vpxenc)
      build_vpxenc
      ;;
    x264)
      build_x264
      ;;
    ffmpeg)
      build_ffmpeg
      ;;
    x265)
      build_x265
      ;;
    hevc)
      build_hevc_hm
      ;;
    openh264)
      build_openh264
      ;;
    libavc)
      build_libavc
      ;;
    *)
      echo "Can't do $1"
      exit 1
  esac
  shift
done
}

# The default is to build everything.
if [ "$#" -eq 0 ]; then
  echo "Building everything"
  build_func vpxenc x264 ffmpeg x265 hevc openh264 libavc
else
  build_func $@
fi

echo "All done"
exit 0
