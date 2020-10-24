#!/usr/bin/env python3
# -*- coding: ascii -*-

import sys
import os
import time
import signal

pidfile = ".runner.pid"
statusfilename = ".runner.status"


#
# open the pidfile and read the process id
#    give an error message if file not found or bad pid
# send the USR1 signal to runner.py
# open the status file for reading and check the size
# wait until it is non zero size, then read contents and copy to output, then quit.
#
# give error messages as necessary

pid_file = open(pidfile, "r")
line = pid_file.readline().strip()
pid = int(line)
pid_file.close()

try:
    os.kill(pid, signal.SIGUSR1)
except ProcessLookupError:
    print("process not found")
    sys.exit()

t = 0
while t <= 5:
    if os.path.isfile(statusfilename):
        if os.stat(statusfilename).st_size > 0:
            status_file = open(statusfilename, "r")
            lines = status_file.readlines()
            while "" in lines:
                lines.remove("")
            if "\n" in lines:
                lines.remove("\n")
            for line in lines:
                line = line.strip("\n")
                print(line)
            status_file.close()
            status_file = open(statusfilename, "w")
            status_file.close()
            sys.exit()
        else:
            if t == 5:
                print("file " + statusfilename + " is empty")
                print("status timeout")
                sys.exit()
            else:
                t = t + 1
                time.sleep(1)
    else:
        if t == 5:
            print("file " + statusfilename + " not found")
            print("status timeout")
            sys.exit()
        else:
            t = t + 1
            time.sleep(1)




