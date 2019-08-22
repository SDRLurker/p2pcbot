#!/bin/bash
while [ 1 ] 
do
    pid=`ps -ef | grep "p2pcbot.py" | grep -v 'grep' | awk '{print $2'}`
    if [ -z $pid ]; then
        nohup python3 p2pcbot.py &
    fi
    sleep 60
done
