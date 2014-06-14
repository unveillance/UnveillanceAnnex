#! /bin/bash

wget -O lib/anaconda.sh http://09c8d0b2229f813c1b93-c95ac804525aac4b6dba79b00b39d1d3.r79.cf1.rackcdn.com/Anaconda-1.9.1-Linux-x86_64.sh
chmod +x lib/anaconda.sh
echo "**************************************************"
echo "Installing Python Framework via ANACONDA"

sleep 10

./lib/anaconda.sh

echo $PATH
source ~/.bashrc
echo $PATH

echo "**************************************************"
echo "Installing other python dependencies..."
pip install --upgrade fabric
python setup.py