#!/bin/bash
ps aux | grep papeet_server.py | awk '{print "kill -9", $2}' | sh
ps aux | grep gui.py | awk '{print "kill -9", $2}' | sh
