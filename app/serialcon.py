# import bluetooth
import os
import time
import serial
import panya
import re
from app import db
from app.models import User, Robot
from datetime import datetime
from app import app
from flask import json, g
from sys import platform as _platform
import sys

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess

# Uncomment the following lines to enable BLE search
# if _platform == "linux" or _platform == "linux2":
# 	from bluetooth.ble import DiscoveryService
# 	blescan = True
# else:
# 	blescan = False

# import filepaths from config file
bdir = app.config["BASE"]
sdir = app.config["DATA"]
# search result from bluetooth legacy discovery stored in resp list
resp = []

# determine which platform this app package is running on and set the
# required shell/bash script paths. these scripts manage all the
# hosts bluetooth pairing and device tree attaching with the robots.
rfpath = os.path.join(bdir,"app","hostcon.sh")
if _platform == "linux" or _platform == "linux2":
	import bluetooth
	host="linux"
elif _platform == "darwin":
	host="darwin"
else:
	import bluetooth
	host="win"

def sketchupl(sketchpath):
	if os.path.exists(sketchpath):
		pass
	try:
		if (host=="win"):
			output=subprocess.call([rfpath,'-h',host,'-s',sketchpath, '-r'], shell=True)
			print '********************************************************************'
			print output
			print '********************************************************************'
		else:
			output=subprocess.call(['%s -h %s -s %s -r' %(rfpath,host,sketchpath)], shell=True)
			print '********************************************************************'
			print output
			print '********************************************************************'
		return True
	except Exception,e:
		print "USB reset of robot failed"
		print str(e)
		return False


def leginquire():
	# bluetooth legacy discovery api endpoint. This endpoint is used by the
	# registration page when searching for nearby bluetooth devices.
	global resp
	global i
	resp = []
	nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True)
	for addr, name in nearby_devices:
		try:
			resp.append({'mac':str(addr),'name':str(name)})
		except UnicodeEncodeError:
			resp.append({'mac':str(addr),'name':str(name.encode('utf-8', 'replace'))})
	
	# ble discovery endpoint. This trigger is a work in progress due to limitations
	# with the pybluez library.
	# if ((resp == []) & (blescan)):
		# bleinquire()

	# jsonify the bluetooth search results to be consumed by the 
	# registration page ajax pull request.
	response = json.dumps(resp)
	return response

def sdpbrowse(macid=None):
	# this function determines the available service profiles at the specified bluetooth macid.
	target = macid
	print "Determining service profiles at "+str(target)
	if target == "all": target = None

	services = bluetooth.find_service(address=target)

	if len(services) > 0:
	    print("found %d services on %s" % (len(services), target))
	    print()
	else:
	    print("no services found")

	for svc in services:
	    print("Service Name: %s"    % svc["name"])
	    print("    Host:        %s" % svc["host"])
	    print("    Description: %s" % svc["description"])
	    print("    Provided By: %s" % svc["provider"])
	    print("    Protocol:    %s" % svc["protocol"])
	    print("    channel/PSM: %s" % svc["port"])
	    print("    svc classes: %s "% svc["service-classes"])
	    print("    profiles:    %s "% svc["profiles"])
	    print("    service id:  %s "% svc["service-id"])
	    print()

def rfcommbind(rfcset,macid,alias=None,unick=None,commands=None,uid=None,flush=None):
	# this function takes the supplied macid passing it to the bash/shell script to
	# pair to using the simple-bluez-agent tool and attach said macid to a 
	# /dev/rfcomm port. If the reset flag is passed, the associated robot macid is 
	# flushed i.e. released from rfcomm and the pairing entry deleted from 
	# /var/lib/bluetooth/{local host macid}/linkkeys. This flushing might be overkill
	# but it ensures that all host-robot sessions are handled robustly.
	if flush is None:
		try:
			if (host=="win"):
				output=subprocess.call([rfpath,'-u',macid,'-d',rfcset,'-h',host, '-p'], shell=True)
				print '********************************************************************'
				print output
				print '********************************************************************'
			else:
				output=subprocess.call(['%s -u %s -d %s -h %s -p' %(rfpath,macid,rfcset,host)], shell=True)
				print '********************************************************************'
				print output
				print '********************************************************************'
			if (output==0):
				print 'Starting command upload procedure'
				datasend(macid,alias,unick,commands,rfcset,uid)
			# elif (output==1):
			# 	print 'Makefile compilation failed'
			# elif (output==2):
			# 	print 'No bluetooth host device found'
			# 	print 'Please plug in a USB bluetooth dongle'
			# 	robot = Robot.query.filter_by(user_id=uid).first()
			# 	robots = Robot.query.all()
			# 	robot.status="inactive"
			# 	db.session.commit()
			# 	for rob in robots:
			# 		print "%s:%s" %(robot.alias,robot.status)
			# elif (output==3):
			# 	print 'Bluetooth pairing procedure failed'
			# 	print 'Please try uploading commands again'
			# 	robot = Robot.query.filter_by(user_id=uid).first()
			# 	robots = Robot.query.all()
			# 	robot.status="inactive"
			# 	db.session.commit()
			# 	for rob in robots:
			# 		print "%s:%s" %(robot.alias,robot.status)
			# elif (output==4):
			# 	print 'Rfcomm binding procedure failed'
			# 	print 'Device dev path probably pre-assigned'
			# 	robot = Robot.query.filter_by(user_id=uid).first()
			# 	robots = Robot.query.all()
			# 	robot.status="inactive"
			# 	db.session.commit()
			# 	for rob in robots:
			# 		print "%s:%s" %(robot.alias,robot.status)
			# elif (output==5):
			# 	print 'Rfcomm release procedure failed'
			# 	print 'Device dev path probably non-existent'
			# 	robot = Robot.query.filter_by(user_id=uid).first()
			# 	robots = Robot.query.all()
			# 	robot.status="inactive"
			# 	db.session.commit()
			# 	for rob in robots:
			# 		print "%s:%s" %(robot.alias,robot.status)
			# elif (output==6):
			# 	print 'Bluetooth client ping failed'
			# 	print 'Please make sure client is powered on and close by'
			# 	robot = Robot.query.filter_by(user_id=uid).first()
			# 	robots = Robot.query.all()
			# 	robot.status="inactive"
			# 	db.session.commit()
			# 	for rob in robots:
			# 		print "%s:%s" %(robot.alias,robot.status)
			# elif (output==7):
			# 	print 'Bluetooth client not registered with buez'
			# 	print 'Host operation might have been compromised'
			# 	robot = Robot.query.filter_by(user_id=uid).first()
			# 	robots = Robot.query.all()
			# 	robot.status="inactive"
			# 	db.session.commit()
			# 	for rob in robots:
			# 		print "%s:%s" %(robot.alias,robot.status)
			# elif (output==8):
			# 	print 'Bluetooth unpairing procedure failed'
			# 	print 'Host operation might have been compromised'
			# 	robot = Robot.query.filter_by(user_id=uid).first()
			# 	robots = Robot.query.all()
			# 	robot.status="inactive"
			# 	db.session.commit()
			# 	for rob in robots:
			# 		print "%s:%s" %(robot.alias,robot.status)
		except Exception,e:
			# if an exception is caught while pairing or dev attaching, the associated
			# robot and macid are flushed to maintain database and device listing integrity.
			# the associated robot status is set to inactive to allow queued connections to
			# be handled.
			robot = Robot.query.filter_by(user_id=uid).first()
			robot.status="inactive"
			db.session.commit()
			print "Error Binding RFCOMM Device"
			# the only error condition that necessitates an automatic client flush
			if (host=="win"):
				output=subprocess.call([rfpath,'-u',macid,'-d',rfcset,'-f','-h',host], shell=True)
			else:
				output=subprocess.call(['%s -u %s -d %s -f -h %s' %(rfpath,macid,rfcset,host)], shell=True)
			print str(e)
	else:
		try:
			# removed the automatic client flush to improve the web client speed.
			# if (host=="win"):
			# 	output=subprocess.call([rfpath,'-u',macid,'-d',rfcset,'-f','-h',host], shell=True)
			# 	print '********************************************************************'
			# 	print output
			# 	print '********************************************************************'
			# else:
			# 	output=subprocess.call(['%s -u %s -d %s -f -h %s' %(rfpath,macid,rfcset,host)], shell=True)
			# 	print '********************************************************************'
			# 	print output
			# 	print '********************************************************************'
			print "Skipping unpairing and release process"
		except Exception,e:
			# if an error occurs while trying to flush and no ORM-related error is provided
			# a error state with the subprocess call can be assumed.
			print "Error Releasing RFCOMM device!"
			print str(e)
		# ensure that robot status is always set back to inactive to ensure subsequent client
		# connections
		robot = Robot.query.filter_by(user_id=uid).first()
		robots = Robot.query.all()
		robot.status="inactive"
		db.session.commit()
		for rob in robots:
			print "%s:%s" %(robot.alias,robot.status)

def datasend(macid,alias,unick,commands,rfcset,uid):
	# this is the command transport mechanism. A serial port is opened at the rfcset
	# declared devport and commands transmitted using the pyserial library.
	# currently in testing, default preset values are sent to the attached robot that
	# must be running the arduino panyabot sketch.
	# future feature to use the standard firmata library to have bidirectional
	# transmission of data (commands and sensor values).
	flush = "y"
	devport = "/dev/"
	devport+=str(rfcset)
	print devport
	ser = serial.Serial(devport)
	print ser
	print 'Sending %s\'s commands to %s, alias:%s' % (unick,macid,alias)
	ser.write('1')
	time.sleep(1)
	ser.write('2')
	time.sleep(1)
	ser.write('?')
	time.sleep(2)
	ser.write('1')
	ser.close()
	# print the stored commands to the terminal window
	for i in range(0,len(commands)):
		print commands[i]
	# after downstream data transmission is completed, the attached robot is flushed.
	rfcommbind(rfcset,macid,None,None,None,uid,flush)
	flush = ""

def rfcommset(robots):
	# this function manages the allocation of rfcomm port numbers to each incoming request.
	# prstlist stores the previously allocated dev numbers that haven't been declared inactive.
	# prstflag indicates that the function must iterate to the lowest unused port number.
	prstlist={}
	prstflag=False

	for robot in robots:
		if (robot.status!="inactive"):
			prstcomm=re.search("rfcomm.",robot.status)
			print 'Found %s registered to %s' %(prstcomm.group(),robot.alias)
			devno=prstcomm.group().strip("rfcomm")
			prstlist['robot.alias']=devno
			prstflag=True

	if prstflag:
		# this conditional and nested loop interate over the values stored
		# in the prstlist to determine what port value to assign for the current
		# request.
		setval=0
		for key, value in prstlist.iteritems():
			if (setval<value):
				setval=value+1
	else:
		# if prstflag is not true, default to assign at port 0 (i.e. /dev/rfcomm0)
		setval=0

	setcomm="rfcomm"+str(setval)
	return setcomm

def portsetup(commands):
	# this function checks if any current robots are attached and in process
	# if there are, the current request is queued until such a time that all
	# prior tranmissions are completed.
	Qflag = False
	Tout = False
	Qout = False
	user = User.query.filter_by(nickname=g.user.nickname).first()
	robot = Robot.query.filter_by(user_id=user.id).first()
	robots = Robot.query.all()
	for rob in robots:
		print "%s:%s" %(robot.alias,robot.status)
		if (rob.status!="inactive"):
			# Wait for 5 seconds and check again if a host-client bluetooth connection is up
			# If elapsed_time is greater than 10 seconds then timeout the process and prompt
			# for database check for any errors found
			print "Queuing bluetooth upload",
			Qflag = True
			queue_start = time.time()
			elapsed_time = time.time() - queue_start
			while (elapsed_time < 5) and not (Qout):
				print ".",
				if (rob.status == "inactive"):
					print 'Slot in queue found'
					Qout = True
				elapsed_time = time.time() - queue_start
			if (elapsed_time > 5) and not Qout:
				print 'Port setup timeout'
				Tout = True
		else:
			Qout=True

		if Qout and not Tout:
			Qflag = False
		else:
			print "Please check database value for the key %s:%s. Database may have been compromised" %(rob.alias,rob.status)
	if not Qflag:
		rfcset=rfcommset(robots)
		robot.status=rfcset
		db.session.commit()
		rfcommbind(str(rfcset),str(robot.macid),str(robot.alias),str(user.nickname),str(commands),str(user.id))
	# sdpbrowse(robot.macid) # HC06 and HC05 bluetooth modules don't advertise an SDP interface. Uncomment if
	# using a module that does. Bug number will be attached to this issue.

def parseblocks(code):
	# this is where blockly code is parsed into a python file with the command list
	# saved in memory for transimission.
	response = json.dumps(code)
	t = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
	savedir = os.path.join(sdir, g.user.nickname)
	if not os.path.exists(savedir):
		os.mkdir(savedir)
	filename = os.path.join(savedir, t+'.py')
	print filename
	target = open(filename,'w')
	target.write(code)
	target.close()
	execfile(filename,globals(),locals())
	# panya.commands.append("COUNT="+str(locals()['count']+1))
	portsetup(panya.commands)
	panya.commands = []
	return response

# Uncomment the following lines to enable BLE search
# def bleinquire():
# 	global resp
# 	global i
# 	service = DiscoveryService()
# 	devices = service.discover(2)
# 	for addr, name in devices.items():
# 		resp.append({'mac*':str(addr),'name*':str(name)})

if __name__ == '__main__':
	# print "OS: %s" % (str(_platform))
	print leginquire()
