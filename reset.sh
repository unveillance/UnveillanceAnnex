#! /bin/bash
source ~/.bash_profile
echo "......... RESETTING UNVEILLANCE ANNEX FROM CONFIG ........."

python reset.py
RESET_RESULT=$?

if ([ $RESET_RESULT -eq 0 ] || [ $RESET_RESULT -eq 1 ])
then
	sleep 2
	python unveillance_annex.py -firstuse

	if [ $RESET_RESULT -eq 1 ]
	then
		sleep 2
		python restore.py
	fi
	
else
	echo "RESET CANCELLED."
fi