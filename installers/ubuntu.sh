#!/bin/bash

set -e

sudo apt-get install -y python-pip

sudo pip install python-magic

sudo apt-get install -y python-pyexiv2

# Install Handbrake CLI
sudo add-apt-repository ppa:stebbins/handbrake-releases
sudo apt-get update
sudo apt-get install handbrake-cli

