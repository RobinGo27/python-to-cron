#!/usr/bin/env python3
# -*- coding: ascii -*-

"""
The configuration file for runner.py will contain one line for each program that is to be run.   Each line has the following parts: 

timespec program-path parameters

where program-path is a full path name of a program to run and the specified time(s), parameters are the parameters for the program,
timespec is the specification of the time that the program should be run.

The timespec has the following format:

[every|on day[,day...]] at HHMM[,HHMM] run

Square brackets mean the term is optional, vertical bar means alternative, three dots means repeated.

Examples:

every Tuesday at 1100 run /bin/echo hello
	every tuesday at 11am run "echo hello"
on Tuesday at 1100 run /bin/echo hello
	on the next tuesday only, at 11am run "echo hello"
every Monday,Wednesday,Friday at 0900,1200,1500 run /home/bob/myscript.sh
	every monday, wednesday and friday at 9am, noon and 3pm run myscript.sh
at 0900,1200 run /home/bob/myprog
	runs /home/bob/myprog every day at 9am and noon


"""

#
# open the configuration file and read the lines, 
# check for errors
# build a list of "run" records that specifies a time and program to run
#

#
# define up the function to catch the USR1 signal and print run records
#

#
# sort run records by time
# take the next record off the list and wait for the time, then run the program
# add a record to the "result" list
# if this was an "every" record", add an adjusted record to the "run" list 
#
# repeat until no more to records on the "run" list, then exit
#
import sys
import os
import time
import datetime
import signal
import collections
# tutor said it is OK to use copy module to copy item in my class object
import copy

# assign the file names and lists that will be used globally
runner_conf_file_name = "runner.conf"
runner_status_file_name = ".runner.status"
runner_pid_file_name = ".runner.pid"
weekday_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# the function for class objects to get the weekday number in the next week (when keyword is "every" or "on")
def get_next_weekday(day):
    today = datetime.datetime.today()
    today_weekday = today.weekday()
    if day > today_weekday:
        delta = day - today_weekday
        format = today + datetime.timedelta(days = delta)
        return format
    else:
        delta = day - today_weekday + 7
        format = today + datetime.timedelta(days = delta)
        return format

# the function for the signal handler (signal from runstatus.py)
def signal_handler(signum, stack_frame):
    runner_status_file = open(runner_status_file_name, "w")
    for command in done_commands:
        runner_status_file.write("ran " + command.time_transfer_format.strftime("%a %b %d %H:%M:%S %Y") + " " + command.program_path + " " + " ".join(command.parameters) + "\n")
    for command in error_commands:
        runner_status_file.write("error " + command.time_transfer_format.strftime("%a %b %d %H:%M:%S %Y") + " " + command.program_path + " " + " ".join(command.parameters) + "\n")
    will_run_command = total_commands[0]
    runner_status_file.write("will run at " + will_run_command.time_transfer_format.strftime("%a %b %d %H:%M:%S %Y") + " " + will_run_command.program_path + " " + " ".join(will_run_command.parameters) + "\n")
    runner_status_file.close()


signal.signal(signal.SIGUSR1, signal_handler)

# build a class to parse each line from runner.conf and store each task as a class object
class RunProgram:
    def __init__(self, fre, day, hour, minute, program_path, parameters):
        # fre is the keyword ("at", "on", "every")
        # time_transfer_format is the standard format that is convenient for me to sort the list based on the running time
        self.fre = fre
        self.day = day
        self.hour = hour
        self.minute = minute
        self.program_path = program_path
        self.parameters = parameters
        self.time_transfer_format = None

    # transfer the time to same standard, convenient to sort then
    def time_transfer(self):
        fre = self.fre
        day = int(self.day)
        hour = int(self.hour)
        minute = int(self.minute)
        format = datetime.datetime.today()
        if fre == "at" and hour > datetime.datetime.now().hour:
            self.time_transfer_format = format.replace(hour = hour, minute = minute, second = 00, microsecond = 00)
        elif fre == "at" and hour == datetime.datetime.now().hour and minute > datetime.datetime.now().minute:
            self.time_transfer_format = format.replace(hour = hour, minute = minute, second = 00, microsecond = 00)
        elif fre == "at" and hour == datetime.datetime.now().hour and minute < datetime.datetime.now().minute:
            tomorrow = format + datetime.timedelta(days = 1)
            self.time_transfer_format = tomorrow.replace(hour = hour, minute = minute, second = 00, microsecond = 00)
        elif fre == "at" and hour < datetime.datetime.now().hour:
            tomorrow = format + datetime.timedelta(days = 1)
            self.time_transfer_format = tomorrow.replace(hour = hour, minute = minute, second = 00, microsecond = 00)
        elif fre == "on" and hour > datetime.datetime.now().hour:
            self.time_transfer_format = format.replace(hour = hour, minute = minute, second = 00, microsecond = 00)
        elif fre == "on" and hour == datetime.datetime.now().hour and minute >= datetime.datetime.now().minute:
            self.time_transfer_format = format.replace(hour = hour, minute = minute, second = 00, microsecond = 00)
        elif fre == "every" and hour > datetime.datetime.now().hour:
            self.time_transfer_format = format.replace(hour = hour, minute = minute, second = 00, microsecond = 00)
        elif fre == "every" and hour == datetime.datetime.now().hour and minute >= datetime.datetime.now().minute:
            self.time_transfer_format = format.replace(hour = hour, minute = minute, second = 00, microsecond = 00)
        else:
            self.time_transfer_format = get_next_weekday(day).replace(hour = hour, minute = minute, second = 00, microsecond = 00)

    # this is especially for the situation that the time now (datetime.datetime.now() is the same as the task running time)
    def time_transfer_special_every(self):
        fre = self.fre
        day = int(self.day)
        hour = int(self.hour)
        minute = int(self.minute)
        format = datetime.datetime.today()
        self.time_transfer_format = get_next_weekday(day).replace(hour = hour, minute = minute, second = 00, microsecond = 00)

    def run(self):
        whole_command = [self.program_path] + self.parameters
        try:
            os.execv(self.program_path, whole_command)
        except OSError:
            date_time_now = datetime.datetime.today().strftime("%a %b %d %H:%M:%S %Y")
            print("error " + date_time_now + self.program_path + " " + " ".join(self.parameters))


pid = str(os.getpid())

try:
    runner_pid_file = open(runner_pid_file_name, "w")
    runner_pid_file.write(pid)
    runner_pid_file.close()
    if not os.path.isfile(runner_status_file_name):
        try:
            runner_status_file = open(runner_status_file_name, "w")
            runner_status_file.close()
        except IOError:
            print("file " + runner_status_file_name + " cannot be created")
            sys.exit()
    else:
        try:
            runner_status_file = open(runner_status_file_name, "r")
        except IOError:
            print("file " + runner_status_file_name + " cannot be opened")
            sys.exit()
except IOError:
    print("file " + runner_pid_file_name + " cannot be created")
    sys.exit()


try:
    conf_file = open(runner_conf_file_name, "r")
    lines = conf_file.readlines()
    conf_file.close()
except IOError:
    print("configuration file not found")
    sys.exit()


total_commands = []
done_commands = []
error_commands = []
while "" in lines:
    lines.remove("")
# print(lines)
while "\n" in lines:
    lines.remove("\n")

# try to find if there is any error
if lines == []:
    print("configuration file empty")
    sys.exit()

if len(lines) != len(set(lines)):
    line = [item for item, count in collections.Counter(lines).items() if count > 1]
    if "\n" in line:
        line.remove("\n")
    print("error in configuration: " + line[0].strip("\n"))
    sys.exit()

# parse each line
for line in lines:
    line = line.strip("\n")
    sentence = line.split(" ")
    while "" in sentence:
        sentence.remove("")
    # detecting errors
    if sentence[0] not in ["at", "on", "every"]:
        print("error in configuration: " + line)
        sys.exit()
    elif sentence[0] == "at":
        if len(sentence) < 4 or sentence[2] != "run":
            print("error in configuration: " + line)
            sys.exit()
        fre = "at"
        day = datetime.datetime.now().weekday()
        program_path = sentence[3]
        parameters = sentence[4:]
        hour_min_list = sentence[1].split(",")
        # detecting errors
        for i in hour_min_list:
            if not i.isdigit() or len(i) != 4 or int(i[0:2]) >= 24 or int(i[2:4]) >= 60:
                print("error in configuration: " + line)
                sys.exit()
        if len(hour_min_list) == 1:
            hour = sentence[1][0:2]
            minute = sentence[1][2:4]
            # detect if the time has passed, if passed, set to tomorrow
            if int(hour) < datetime.datetime.now().hour or (hour == datetime.datetime.now().hour and int(minute) < datetime.datetime.now().minute):
                if day == 6:
                    day = 0
                else:
                    day = day + 1
                    total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))
            else:
                total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))
        else:
            for each_hour_min in hour_min_list:
                hour = each_hour_min[0:2]
                minute = each_hour_min[2:4]
                if int(hour) < datetime.datetime.now().hour or (hour == datetime.datetime.now().hour and int(minute) < datetime.datetime.now().minute):
                    if day == 6:
                        day = 0
                    else:
                        day = day + 1
                        total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))
                else:
                    total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))

    elif sentence[0] == "on":
        if len(sentence) < 6 or sentence[4] != "run" or sentence[2] != "at":
            print("error in configuration: " + line)
            sys.exit()
        fre = "on"
        program_path = sentence[5]
        parameters = sentence[6:]
        day_list = sentence[1].split(",")
        hour_min_list = sentence[3].split(",")
        for i in hour_min_list:
            if not i.isdigit() or len(i) != 4 or int(i[0:2]) >= 24 or int(i[2:4]) >= 60:
                print("error in configuration: " + line)
                sys.exit()
        if len(day_list) != len(set(day_list)):
            print("error in configuration: " + line)
            sys.exit()
        for day in day_list:
            if day not in weekday_list:
                print("error in configuration: " + line)
                sys.exit()
        if len(day_list) == 1:
            day = weekday_list.index(day_list[0])
            if len(hour_min_list) == 1:
                hour = sentence[3][0:2]
                minute = sentence[3][2:4]
                total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))
            else:
                for each_hour_min in hour_min_list:
                    hour = each_hour_min[0:2]
                    minute = each_hour_min[2:4]
                    total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))
        else:
            for each_day in day_list:
                day = weekday_list.index(each_day)
                if len(hour_min_list) == 1:
                    hour = sentence[3][0:2]
                    minute = sentence[3][2:4]
                    total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))
                else:
                    for each_hour_min in hour_min_list:
                        hour = each_hour_min[0:2]
                        minute = each_hour_min[2:4]
                        total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))
    elif sentence[0] == "every":
        if len(sentence) < 6 or sentence[4] != "run" or sentence[2] != "at":
            print("error in configuration: " + line)
            sys.exit()
        fre = "every"
        program_path = sentence[5]
        parameters = sentence[6:]
        day_list = sentence[1].split(",")
        hour_min_list = sentence[3].split(",")
        for i in hour_min_list:
            if not i.isdigit() or len(i) != 4 or int(i[0:2]) >= 24 or int(i[2:4]) >= 60:
                print("error in configuration: " + line)
                sys.exit()
        if len(day_list) != len(set(day_list)):
            print("error in configuration: " + line)
            sys.exit()
        for day in day_list:
            if day not in weekday_list:
                print("error in configuration: " + line)
                sys.exit()
        if len(day_list) == 1:
            day = weekday_list.index(day_list[0])
            if len(hour_min_list) == 1:
                hour = sentence[3][0:2]
                minute = sentence[3][2:4]
                total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))
            else:
                for each_hour_min in hour_min_list:
                    hour = each_hour_min[0:2]
                    minute = each_hour_min[2:4]
                    total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))
        else:
            for each_day in day_list:
                day = weekday_list.index(each_day)
                if len(hour_min_list) == 1:
                    hour = sentence[3][0:2]
                    minute = sentence[3][2:4]
                    total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))
                else:
                    for each_hour_min in hour_min_list:
                        hour = each_hour_min[0:2]
                        minute = each_hour_min[2:4]
                        total_commands.append(RunProgram(fre, day, hour, minute, program_path, parameters))

for command in total_commands:
    command.time_transfer()

time_test = []
for command in total_commands:
    time_test.append(command.time_transfer_format)
    if len(time_test) != len(set(time_test)):
        time_dup = [item for item, count in collections.Counter(time_test).items() if count > 1]
        print("error in configuration: " + "duplicate time")
        sys.exit()


total_commands.sort(key = lambda command: command.time_transfer_format)
# for i in total_commands:
#     print("time: " + str(i.time_transfer_format))

while True:
    command_to_run = total_commands[0]
    time_now = datetime.datetime.now().replace(second = 00, microsecond = 00)
    if time_now == command_to_run.time_transfer_format:
        error = False
        try:
            if os.fork() == 0:
                command_to_run.run()
            else:
                os.wait()
        except OSError:
            date_time = datetime.datetime.today().strftime("%a %b %d %H:%M:%S %Y")
            print("error " + date_time + command_to_run.program_path + " " + " ".join(command_to_run.parameters))
            error = True

        if not error:
            done_commands.append(command_to_run)
        else:
            error_commands.append(command_to_run)

        if command_to_run in total_commands:
            total_commands.remove(command_to_run)
        else:
            pass
        # decide if this is the special situation that running time equals to the time now (datetime.datetime.now())
        if command_to_run.fre == "every" and (int(command_to_run.hour) != datetime.datetime.now().hour or int(command_to_run.minute) != datetime.datetime.now().minute):
            command_to_run.time_transfer()
            total_commands.append(command_to_run)
        elif command_to_run.fre == "every" and int(command_to_run.hour) == datetime.datetime.now().hour and int(command_to_run.minute) == datetime.datetime.now().minute:
            dup = copy.deepcopy(command_to_run)
            dup.time_transfer_special_every()
            total_commands.append(dup)
    if len(total_commands) == 0:
        print("nothing left to run")
        sys.exit()
    time.sleep(1)






