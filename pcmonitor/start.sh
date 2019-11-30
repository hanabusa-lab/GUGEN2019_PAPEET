#!/bin/bash
cur=$PWD
echo $cur
cd $cur/flask
echo $PWD 
python3 papeet_server.py&
cd $cur/gui
echo $PWD 
python3 gui.py& 
