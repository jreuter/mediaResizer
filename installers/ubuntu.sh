#!/bin/bash

set -e

sudo apt-get install -y python3-pip

pip3 install --user python-magic gexiv2-2

sudo apt-get install -y libgexiv2-2

# Install Handbrake CLI
sudo add-apt-repository ppa:stebbins/handbrake-releases
sudo apt-get update
sudo apt-get install handbrake-cli

