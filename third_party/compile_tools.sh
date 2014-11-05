#!/bin/sh
#
# Compile and install required software tools to run the tests.
#
# This script has been tested on Ubuntu, Trusty Tahr.
#
set -e

TOOLDIR=$CODEC_TOOLPATH
if [ -z "$TOOLDIR" -o ! -d "$TOOLDIR" ]; then
  echo Tooldir not set correctly: $TOOLDIR
  echo "Did you run init.sh?"
  exit 1
fi

echo $TOOLDIR
# Requirements for compiling libvpx.
sudo apt-get install yasm

# Build the vpxenc and vpxdec binaries
if [ ! -d libvpx ]; then
  git clone http://git.chromium.org/webm/libvpx.git
fi
cd libvpx
# Ensure we check out exactly a consistent version.
git checkout -f master
#git checkout v1.3.0
# Check out the Oct 20 2014 version of libvpx.
git checkout 9c98fb2bab6125a0614576bf7635981163b1cc79
./configure
# Leftovers from previous compilations may be troublesome.
make clean
# There's something wrong in the make for libvpx at this version.
# Ignore the result code from make. We'll bail if vpxenc and vpxdec
# were not built.
make || echo "Something went wrong building libvpx, continuing"
cp vpxenc $TOOLDIR
cp vpxdec $TOOLDIR

# Build a patched version of vpxenc that supports setting
# the q-value for key-frames, golden frames and alt-frames separately
# from the generic fixed q value that is used for all other frames.
patch -p1 < ../vp8_fixed_q.patch
make
cp vpxenc $TOOLDIR/vpxenc-mpeg

cd ..


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
cd ..

# Build the ffmpeg binary.
if [ ! -d ffmpeg ]; then
  git clone git://source.ffmpeg.org/ffmpeg.git ffmpeg
fi
cd ffmpeg
git checkout ae04493
./configure
make ffmpeg
cp ffmpeg $TOOLDIR
make ffprobe
cp ffprobe $TOOLDIR
cd ..

# Build the psnr binary.
gcc -o $TOOLDIR/psnr src/psnr.c -lm


