#!/bin/bash

set -e

sudo apt-get install -y python3-pip

pip3 install --user python-magic

sudo apt-get install -y libgexiv2-2

pip3 install --user python-magic ffmpeg-python pyexiftool Pillow
pip3 install psutil pymediainfo pytz

sudo apt-get install -y libgexiv2-2 python3-pymediainfo
sudo apt-get install gir1.2-gexiv2-0.10 python3-gi libgirepository1.0-dev

# Install Handbrake CLI
#sudo add-apt-repository ppa:stebbins/handbrake-releases
#sudo apt-get update
#sudo apt-get install handbrake-cli

