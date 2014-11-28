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
# Install all required software for the codec comparision tool.
#
# The initial version pulls in the vpx_codec_comparison repository,
# and runs the install script from there. Things might migrate up later.
#
set -e

# Requirements for compiling libvpx.
sudo apt-get install yasm

# More tools called by the scripts
sudo apt-get install mkvtoolnix
# Install prerequisites for running Jekyll as a web server
sudo apt-get install ruby1.9.1-dev
sudo apt-get install nodejs
# Jekyll 2.4.0 depends on redcarpet.
# Redcarpet 3.1.2 depends on ruby 1.9.2 or later.
# redcarpet 3.0.0 is installable under 1.9.1.
# celluloid-0.16.0 has the same problem.
# So we limit to a jekyll version that builds under 1.9.1.
sudo gem install jekyll -v 1.5.1

# Compile from source everything that needs compiling.
./compile_tools.sh

echo "All software installed"


