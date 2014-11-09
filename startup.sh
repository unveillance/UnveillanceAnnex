#! /bin/bash
source ~/.bash_profile
python unveillance_annex.py -start

if [ $# -eq 1 ]
then
	tail -f .monitor/api.log.txt
fi