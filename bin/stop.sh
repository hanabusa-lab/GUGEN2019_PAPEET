#!/bin/bash
ps aux | grep papeet_main | awk '{print "kill -9", $2}' | sh
ps aux | grep led_mgr | awk '{print "kill -9", $2}' | sh
ps aux | grep serv_mgr | awk '{print "kill -9", $2}' | sh
