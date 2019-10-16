#!/bin/bash

#dont execute if main.py is running 
psnum=`ps aux | grep main.py | wc -l`

#echo $psnum
if [ $psnum -gt 1 ]; then
echo "process is running. process num=[$psnum]. stop"
exit
else 
echo "process is not running. process num=[$psnum]. exec process"
fi

#cd /pet/bin

#exec pet_mgr.py
sudo python3 papeet_main.py& 
#exec led_mgr.py
sudo python3 led_mgr.py& 
sudo python3 serv_mgr.py& 
