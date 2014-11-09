#! /bin/bash
if [ $# -eq 0 ]
then
	TARG=api
else

	TARGS=(api els worker)
	if `echo ${TARGS[@]} | grep -q "$1"`
	then
		TARG=$1
	else
		TARG=api
	fi
fi

tail -f $(pwd)/.monitor/$TARG.log.txt