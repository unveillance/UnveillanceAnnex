#! /bin/bash
python unveillance_annex.py -stop
echo "......... RESETTING UNVEILLANCE ANNEX FROM CONFIG ........."
sleep 5
python reset.py
sleep 2
python unveillance_annex.py -firstuse