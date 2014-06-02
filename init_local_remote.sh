!# /bin/bash
THIS_DIR=`pwd`

KEY_FILE=$1

if [ $# -eq 2 ]
then
	SSH_ROOT=~/.ssh
else
	SSH_ROOT=$2
fi

cat $1 > $SSH_ROOT/authorized_keys