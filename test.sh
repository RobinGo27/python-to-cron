#!/bin/bash

echo "every Tuesday at 1100 run /bin/echo hello world" > runner.conf
chmod u+x runner.py
python3 runner.py
sleep 5s
chmod u+x runstatus.py
python3 runstatus.py