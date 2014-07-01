#!/bin/bash
#
# Install all required software for the codec comparision tool.
#
# The initial version pulls in the vpx_codec_comparison repository,
# and runs the install script from there. Things might migrate up later.
#
set -e

if [ ! -d vpx_codec_comparison ]; then
  git clone http://git.chromium.org/webm/vpx_codec_comparison.git
fi
cd vpx_codec_comparison
git pull
# Note: We clobber all local changes to this repository by doing this.
git checkout -f master
./install_software.sh
cd ..

# Install prerequisites for running Jekyll as a web server
sudo apt-get install ruby1.9.1-dev
sudo apt-get install nodejs
sudo gem install jekyll

# More stuff will go here.

echo "All software installed"


