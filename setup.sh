#! /bin/bash
THIS_DIR=`pwd`

if [ $# -eq 0 ]
then
	LAUNCH_ANNEX=true
	WITH_CONFIG=0
else
	LAUNCH_ANNEX=false
	WITH_CONFIG=$1
fi

brew install wget libmagic

PYTHON_VERSION=$(which python)
if [[ $PYTHON_VERSION == *anaconda/bin/python ]]
then
	echo "ANACONDA already installed.  Skipping"
else
	wget -O lib/anaconda.sh https://3230d63b5fc54e62148e-c95ac804525aac4b6dba79b00b39d1d3.ssl.cf1.rackcdn.com/Anaconda-2.3.0-MacOSX-x86_64.sh
	chmod +x lib/anaconda.sh
	echo "**************************************************"
	echo "Installing Python Framework via ANACONDA"

	sleep 10
	./lib/anaconda.sh
	sleep 3

	ANACONDA=$(grep "anaconda" ~/.bashrc)
	echo $ANACONDA >> ~/.bash_profile
	sleep 3
fi

source ~/.bash_profile

cd lib/Core
pip install -r requirements.txt

cd $THIS_DIR
pip install -r requirements.txt

cd lib/socksjs-tornado
python setup.py install

cd ../python-magic
python setup.py install

cd $THIS_DIR
echo "**************************************************"
python setup.py $WITH_CONFIG
source ~/.bash_profile

sleep 2
if $LAUNCH_ANNEX; then
	chmod 0400 conf/*
	python unveillance_annex.py -firstuse
fi
