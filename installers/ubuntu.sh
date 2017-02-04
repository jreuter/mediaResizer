#!/bin/bash

set -e

# Install Handbrake CLI
sudo add-apt-repository ppa:stebbins/handbrake-releases
sudo apt-get update

sudo apt-get install -y python-pip python-setuptools python-pyexiv2 python-imaging handbrake-cli

sudo pip install python-magic

