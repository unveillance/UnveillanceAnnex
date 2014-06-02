#! /bin/bash
THIS_DIR=`pwd`
USER_CONFIG=$THIS_DIR/conf/annex.config.yaml
echo base_dir: $THIS_DIR >> $USER_CONFIG

if [ $# -eq 0 ]
then
	echo "no initial args"
	OLD_DIR=$THIS_DIR
	ANNEX_DIR=/home/danse/unveillance_remote
	ANACONDA_DIR=/home/danse/anaconda
else
	OLD_DIR=$1
	ANNEX_DIR=$2
	ANACONDA_DIR=$3
	echo "inital args: $1 $2 $3"
fi

mkdir $THIS_DIR/.monitor
mkdir $ANNEX_DIR

echo annex_dir: $ANNEX_DIR >> $USER_CONFIG

echo "**************************************************"
echo "Installing ELASTICSEARCH and GIT-ANNEX"
wget -O lib/elasticsearch.tar.gz https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.0.1.tar.gz
tar -xvzf lib/elasticsearch.tar.gz -C lib
rm lib/elasticsearch.tar.gz

wget -O lib/git-annex.tar.gz http://downloads.kitenet.net/git-annex/linux/current/git-annex-standalone-amd64.tar.gz
tar -xvzf lib/git-annex.tar.gz -C lib
rm lib/git-annex.tar.gz

PATH_APPEND=$PATH

for f in lib/*
do
	if echo "$f" | grep '^lib/elasticsearch*' >/dev/null ; then
		echo els_root: $f/bin/elasticsearch >> $USER_CONFIG
		break
	fi
	
	if echo "$f" | grep '^lib/git-annex*' >/dev/null ; then
		PATH_APPEND=$PATH_APPEND:$THIS_DIR/$f
		break
	fi
done

wget -O lib/anaconda.sh http://09c8d0b2229f813c1b93-c95ac804525aac4b6dba79b00b39d1d3.r79.cf1.rackcdn.com/Anaconda-1.9.1-Linux-x86_64.sh
chmod +x lib/anaconda.sh
echo "**************************************************"
echo "Installing Python Framework via ANACONDA"

sleep 10

echo "**************************************************"
echo "NOTE:  WHEN PROMPTED, SET ANACONDA'S INSTALL PATH TO"
echo ""
echo $ANACONDA_DIR
echo ""
echo "DO NOT SET THE ~/.bashrc VARIABLE.  IT IS DONE FOR YOU."
echo "**************************************************"

./lib/anaconda.sh

PATH_APPEND=$ANACONDA_DIR/bin:$PATH_APPEND
echo export PATH=$PATH_APPEND >> ~/.bashrc
echo $PATH
source ~/.bashrc
echo $PATH

echo "**************************************************"
echo "Installing other python dependencies..."
pip install --upgrade -r requirements.txt