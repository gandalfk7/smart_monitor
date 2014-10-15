#! /usr/bin/env python

import subprocess
import os
import time
import sys
import logging
import smtplib
from smart_monitor_config import *

warning = 0	#this is the variable that triggers the mail, if it's 0 there are no prob, if it's 1 then we have a problem

#sendmail
def sendemail(from_addr, to_addr_list, cc_addr_list,
              subject, message,
              login, password,
              smtpserver='smtp.gmail.com:587'):
    header  = 'From: %s\n' % from_addr
    header += 'To: %s\n' % ','.join(to_addr_list)
    header += 'Cc: %s\n' % ','.join(cc_addr_list)
    header += 'Subject: %s\n\n' % subject
    message = header + message
    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(login,password)
    problems = server.sendmail(from_addr, to_addr_list, message)
    server.quit()

#define log variables
logger = logging.getLogger('smart_monitor')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/scripts/logs/smart_monitor.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
##

#prepare logfile
date = str(os.popen("date").read())		#read the time+date from the os
open('/scripts/smart_monitor.mailfile', 'w').close() 	#open file and erase it's content
file = open("/scripts/smart_monitor.mailfile", "r+") 	#open file for writing
file.write(date + "\n")				#write the date in the file

#gets the list of the disks to check
fileName=open("/scripts/smart_monitor.list")          #open the vm list file
dirty_disks = [i for i in fileName.readlines()]        #acquire the lines dirty with newlines and spaces
disks = [item.rstrip() for item in dirty_disks]          #strips the newline from the elements in the list

#MAIN LOOP:
logger.info("starting disk check")			#logs the start of the main loop
for disk in disks:
	logger.info("checking disk: " + disk)		#logs the check
	diskstatus = str(os.popen("smartctl -H /dev/" + disk).read()) #gets the status of the disk from smartmontools
#	file.write(disk + " status is: " + diskstatus + "\n")
#	diskstatus = "PASSED fail"
	if "#" in disk: 
		logger.warning("skipped disk: " + disk)
		disk_nocheck = disk.replace("#","")
		diskstatus = str(os.popen("smartctl -H /dev/" + disk_nocheck).read())
		file.write(disk + " has been skipped from the check, is this ok? diskstatus: " + "\n")
		file.write(diskstatus + "\n")
		warning = 1
		continue
	#diskstatus = str(os.popen("smartctl -H /dev/" + disk + ' | grep -i \"SMART overall-health self-assessment test result: \"').read())
	if "PASSED" in diskstatus and not "FAIL" in diskstatus and not "fail" in diskstatus: logger.info(disk + " is OK and reports: " + diskstatus)
	else: 
		logger.critical("WARNING DISK: " + disk + " STATUS: " + diskstatus)
		file.write(disk + " IS NOT OK, status: " + "\n")
		file.write(diskstatus + "\n")
		warning = 1

file.close() 

with open ("/scripts/smart_monitor.mailfile", "r") as myfile:		#reopen the logfile
	mailbody = myfile.read().replace('\n', ' \r ')		#read the mailfile and store it in mailbody
myfile.close()

#send email:
#warning = 1    #to test the email sending uncomment this line
if warning <> 0:
	sendemail(from_addr  = mail_from, 
         	to_addr_list = mail_to,
          	cc_addr_list = mail_cc, 
          	subject      = mail_subj, 
          	message      = str(mailbody), 
          	login        = mail_login, 
          	password     = mail_pass)

