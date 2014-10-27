#!/bin/bash
#
# Install all required software for the codec comparision tool.
#
# The initial version pulls in the vpx_codec_comparison repository,
# and runs the install script from there. Things might migrate up later.
#
set -e

cd third_party
./compile_tools.sh
# Exit vpx_codec_comparison
cd ..
# More tools called by the scripts
sudo apt-get install mkvtoolnix
# Install prerequisites for running Jekyll as a web server
sudo apt-get install ruby1.9.1-dev
sudo update-alternatives --set ruby /usr/bin/ruby1.9.1
sudo apt-get install nodejs
# Jekyll 2.4.0 depends on redcarpet.
# Redcarpet 3.1.2 depends on ruby 1.9.2 or later.
# redcarpet 3.0.0 is installable under 1.9.1.
# celluloid-0.16.0 has the same problem.
# So we limit to a jekyll version that builds under 1.9.1.
sudo gem install jekyll -v 1.5.1

echo "All software installed"


