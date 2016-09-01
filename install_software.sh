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
# Install all required software for the codec comparison tool.
#
# The initial version pulls in the vpx_codec_comparison repository,
# and runs the install script from there. Things might migrate up later.
#
set -e

MODE=full
if [ "$1" = "travis" ]; then
  MODE=nocompile
fi

# Requirements for compiling various packages and scripts.
sudo apt-get install yasm mkvtoolnix mercurial cmake cmake-curses-gui \
  build-essential yasm nasm python-numpy

# Install prerequisites for running Jekyll as a web server
sudo apt-get install ruby1.9.1-dev nodejs
# Jekyll 2.4.0 depends on redcarpet.
# Redcarpet 3.1.2 depends on ruby 1.9.2 or later.
# redcarpet 3.0.0 is installable under 1.9.1.
# celluloid-0.16.0 has the same problem.
# So we limit to a jekyll version that builds under 1.9.1.
sudo gem install jekyll -v 1.5.1

# Python packages
sudo pip install y4m

# Install depot_tools - we use the pylint from there
rm -rf third_party/depot_tools
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git \
   third_party/depot_tools

# Compile from source everything that needs compiling.
if [ "$MODE" != "nocompile" ]; then
  ./compile_tools.sh
fi

echo "All software installed"
