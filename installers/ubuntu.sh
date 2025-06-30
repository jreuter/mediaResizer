#!/bin/bash

set -e

sudo apt-get install -y python3-pip

# If Ubuntu Version supports exiftool 12.15 or newer.  Check with `exiftool -ver`
sudo apt-get install -y libimage-exiftool-perl

#Compile from source.  Reference: https://exiftool.org/install.html#Unix
wget https://exiftool.org/Image-ExifTool-13.09.tar.gz
gzip -dc Image-ExifTool-13.09.tar.gz | tar -xf -
cd Image-ExifTool-13.09
perl Makefile.PL
make test
sudo make install

pip3 install --user python-magic ffmpeg-python pyexiftool Pillow
pip3 install psutil pymediainfo pytz
# Couldn't find gexiv2-2

sudo apt install libcairo2-dev libgirepository-2.0-dev
#pip3 install pycairo
pip3 install PyGObject filemime

# python3-pymediainfo is for getting creation date in video files.
# libgexiv2-2 is to get metadata from images.
sudo apt-get install -y libgexiv2-2 python3-pymediainfo

sudo apt-get install gir1.2-gexiv2-0.10 python3-gi libgirepository1.0-dev

# Install Handbrake CLI
#sudo add-apt-repository ppa:stebbins/handbrake-releases
#sudo apt-get update
#sudo apt-get install handbrake-cli

