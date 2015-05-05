#!/bin/sh
#
# This file should be sourced before doing work in the compare-codecs
# environment.
#

# Function to remove duplicate path entries - to make running this file
# twice not grow the path. It also trims leading colons.
dedup() {
  echo $1 | awk -F: '{for (i=1;i<=NF;i++) { if ( $i != "" && !x[$i]++ ) printf("%s:",$i); }}' | sed -e 's/:*$//'
}

if [ ! -f init.sh ]; then
  echo "This init file must be sourced while in its own directory"
  exit 1
fi

export WORKDIR=$PWD
PATH=$(dedup "$PATH:$WORKDIR/bin")
export PYTHONPATH=$(dedup "$PYTHONPATH:$WORKDIR/lib")
export CODEC_WORKDIR=$WORKDIR/workdir
export CODEC_TOOLPATH=$WORKDIR/tools
if [ -d $WORKDIR/score_storage ]; then
  export CODEC_SCOREPATH=$WORKDIR/score_storage
else
  export CODEC_SCOREPATH=''
fi

if [ ! -d $CODEC_WORKDIR ]; then
  mkdir $CODEC_WORKDIR
fi
if [ ! -d $CODEC_TOOLPATH ]; then
  mkdir $CODEC_TOOLPATH
fi

