#!/bin/bash

set -e

sudo apt-get install -y python3-pip python-setuptools python-pil handbrake-cli

# If Ubuntu Version supports exiftool 12.15 or newer.  Check with `exiftool -ver`
sudo apt-get install -y libimage-exiftool-perl

#Compile from source.  Reference: https://exiftool.org/install.html#Unix
if [ ! -f "Image-ExifTool-13.33.tar.gz" ]; then
  echo "Downloading Image-ExifTool from Sourceforge"
  wget -O "Image-ExifTool-13.33.tar.gz" "https://downloads.sourceforge.net/project/exiftool/Image-ExifTool-13.33.tar.gz?ts=gAAAAABoj1gNcmWRuIlpNTsUwcYiredrPovvJ2Teq0_nz6CaMGaz1Vr71fyQ2ufu7mRRhkKSUi4WnM5gDBCIVJ4p6_vIpTkR9A%3D%3D&r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fexiftool%2Ffiles%2FImage-ExifTool-13.33.tar.gz%2Fdownload"
  echo "Extracting Image-ExifTool"
  gzip -dc Image-ExifTool-13.33.tar.gz | tar -xf -
  echo "Building Image-ExifTool"
  cd Image-ExifTool-13.33
  perl Makefile.PL
  make test
  echo "Installing Image ExifTool"
  sudo make install
fi

echo "Installing Pythong dependencies"
pip3 install --user python-magic ffmpeg-python pyexiftool

# python3-pymediainfo is for getting creation date in video files.
# libgexiv2-2 is to get metadata from images.
sudo apt-get install -y libgexiv2-2 python3-pymediainfo

# Install Handbrake CLI
#sudo add-apt-repository ppa:stebbins/handbrake-releases
#sudo apt-get update


