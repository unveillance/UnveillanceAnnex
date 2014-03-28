#! /bin/bash
OLD_DIR=`pwd`

USER_CONFIG=$OLD_DIR/conf/user.config.yaml
ANNEX_DIR=/home/unveillance_remote

mkdir $OLD_DIR/.monitor
mkdir $ANNEX_DIR
mkdir /var/run/sshd

echo annex_dir: $ANNEX_DIR >> $USER_CONFIG
echo base_dir: $OLD_DIR >> $USER_CONFIG

echo "**************************************************"
echo "Installing ELASTICSEARCH"
wget -O lib/elasticsearch.tar.gz https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.0.1.tar.gz

tar -xvzf lib/elasticsearch.tar.gz -C lib
rm lib/elasticsearch.tar.gz

for f in lib/*
do
	if echo "$f" | grep '^lib/elasticsearch*' >/dev/null ; then
		echo els_root: $f/bin/elasticsearch >> $USER_CONFIG
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
echo "/home/anaconda"
echo ""
echo "DO NOT SET THE ~/.bashrc VARIABLE.  IT IS DONE FOR YOU."
echo "**************************************************"

./lib/anaconda.sh

echo export PATH=/home/anaconda/bin:$PATH >> .bashrc
source .bashrc

echo "**************************************************"
echo "Installing other python dependencies..."
pip install --upgrade -r requirements.txt

cd lib/python-gnupg
make install
cd $OLD_DIR

ANNEX_EXTRAS_DIR=$OLD_DIR/annex_extras
has_extras=$(find $OLD_DIR -type -d -name "annex_extras")
if [[ -z "$has_extras" ]]
then
	echo "(no external packages to add to Annex...)"
else
	echo "**************************************************"
	echo "Running external configurations (-PRE)..."

	cd $ANNEX_EXTRAS_DIR
	chmod +x init_annex_extras_pre.sh
	./init_annex_extras_pre.sh $OLD_DIR
	cd $OLD_DIR