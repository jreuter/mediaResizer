#!/bin/bash

set -e

sudo apt-get install -y python3-pip

pip3 install --user python-magic gexiv2-2 ffmpeg-python

# python3-pymediainfo is for getting creation date in video files.
# libgexiv2-2 is to get metadata from images.
sudo apt-get install -y libgexiv2-2 python3-pymediainfo

# Install Handbrake CLI
sudo add-apt-repository ppa:stebbins/handbrake-releases
sudo apt-get update
sudo apt-get install handbrake-cli

