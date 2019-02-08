#!/usr/bin/python
# -*- coding: utf-8 -*-

# TO DO / Notes: 
#		 1. TLE data gets cached into TLE.txt, but once TLE.txt exists, it won't get updated. 
#		     Need to do a check every now and then to update this file.
# 	     2. Figure out ephem.now() and time.gmtime() objects and why they disagree. Temp fix
#		     was to hard-code the time diff
#		 N. Stellarium can lag behind on satellites/bodies within the solar system and needs
#			to be refreshed (restarted) sometimes
#		 N. ArduinoTelescope folder (one level up) has some .cpp libraries for telescope pointing
#			like 2-star calibration (see CoordsLib.cpp)
# Stellarium Protocol

#LENGTH (2 bytes, integer): length of the message
#TYPE (2 bytes, integer): 0
#TIME (8 bytes, integer): current time on the server computer in microseconds
#    since 1970.01.01 UT. Currently unused.
#RA (4 bytes, unsigned integer): right ascension of the telescope (J2000)
#    a value of 0x100000000 = 0x0 means 24h=0h,
#    a value of 0x80000000 means 12h
#DEC (4 bytes, signed integer): declination of the telescope (J2000)
#    a value of -0x40000000 means -90degrees,
#    a value of 0x0 means 0degrees,
#    a value of 0x40000000 means 90degrees
#STATUS (4 bytes, signed integer): status of the telescope, currently unused.
#    status=0 means ok, status<0 means some error

# UODATES
# 01/07/2015
#	- Adding support for a PS3 controller utilizing the pyGame library
# 01/10/2015
#	- Improved and debugged the communication protocol 
#	- Added target acquisition and updating methods
# 01/11/2015
#	- Adding back the reference star-finding code -- needs work
# 04/06/2015
#	- Re-discovered code, renaming, preparing hardware
#	- Downtime the result of PhD defense and starting job
#	- Reacquainted myself with the software, made some small changes to get
#	  PS3 controller working again (pygame.joystick.init() was ret. false)
# 04/07/2015
#	- Added PS3 controller speed selection
# 04/08/2015
#	- Added temporary code segments for tracking testing
# 04/19/2015
#	- Added a few features for setting reference stars -- checked code
#	- See items below under "Alignment" in Changes
# 04/20/2015
# 	- Refactored code s.t. classes were branched out into modules (communicate, controller, satellite)
# 07/03/2016
#	- Man, I'm bad at finishing projects
# 07/04/2016
#	- Happy birthday, America!
#	- Added keyboard input (arrow keys) with movement speed ramped by press duration -- only tested with stellarium for now
# 07/05/2016
#	- Added module: satinfo.py to handle satellite meta data processing (reading TLEs, getting visible satellites, getting magnitudes)
# 07/06/2016
# 	- Added intercept code. Needs to be modularized
# 07/07/2016
#	- Debugged intercept code and verified it works.
#	- Satellites/planetary bodies were slightly off in stellarium vs. pyephem. Restarting Stellarium fixed this
# 07/09/2016
#	- Added telecoords.py module
#	- This module handles the coordiante transformations (2/3 star calibration)
# 07/22/2016
#	- Last week or two has been spent with hardware dev. (new components, 3d printed parts, etc)
#	- Re-established device control
# 07/23/2016
#	- Arduino testing
#	- Accepts keyboard control for motor axes
# 07/24/2016
#	- Offloaded encoders to second arduino
#	- Added optical interrupt sensor to Alt Axis (need to add one to az axis too)
#	- Changes to communicate module
# 07/26/2016
#	- Efforts over the past few days to try and calibrate the mechanics (figure out encoder/motor pos. accuracy)
#	- Need a base truth, using a camera with macro setup, but this isn't precise enough without an overlay
# 07/30/2016
#	- Will make modications to the embeded code later to determine if there ae issues with encoders and comm interrupts
# 08/08/2016
#	- Comms were not the issue. Azimuth axis works flawlessesly. Could also be interference on the lines. 
#     Encoders subject to signal noise?

# Notes:
# -- Pygame Keyboard Input
#	- pygame events should be pumped at end of processing
#	- pygame needs focus to process input -- can force by using set_grab()
#			preferred: create a display window that can be selected

# Challenges:
# -- Alignment:
#	 This may be the most difficult problem I face, and I am not even sure
#	  it can be addressed successfully. 
#	 Sources of mis-alignment include:
#	 	1. Placement and difficulty of manually orienting
#		2. Design flaws (axes not being perpendicular)
#		3. Uneven surface (entire axis tilted)
#	 Other sources of error:
#		1. Inconsistincy in motor steps/degree
#		2. Slop in gears when changing direction 
#		3. Inaccurate feedback from encoders
#	 The latter two can be addressed using optical encoders to get feedback,
#		that way, position is based off a measurement, and not an assumption.
#	 The first 3 issues require an alignment/calibration scheme, the complexity
#		of which determines the accuracy. 
#
# -- GoTo mechanical limitations:
#	 Write a procedure that paths go-tos above the horizon, and in a way that cable
#		anagement is taken into account (i.e. we can't pass 0/360 in either direction)

# Changes that need to be made:
# -- Interpolation scheme, I think Arduino should do the interpolation
#	- How this might work:
#		1. Arduino receives current position if acquiring new object
#		2. Arduino slews to target
#		3. Meanwhile, Python continuously sends new coordinate (+1s)
#		4. Arduino acquires target
#		5. Arduino sets slew speed based on distance it needs to travel in 1 second
#			(linear interpolation del(Alt)/s, del(Az)/s)
#	- Add a sanity check for the celestial calculations. Time could be wrong, or a 
#		database may need to be updated. Don't want to have to debug this.
#   - Accuracy of encoder feedback / Accuracy of motor positioning needs to be determined

# Proposed Features
# -- Automatic target acquisition mode
#	- How this might work:
#		1. Python sorts satellite list by targets that are up and visible then 
#			by targets that are rising and will be visible soon
#		2. Of "up" targets, Python picks the one with the longest visible time
#		3. Python always prioritize manned-missions, or objects of interest
#		4. If no up targets, or if a target of higher interest is rising, Python
#			preps for new acquisition
#		5. If no up targets, Python slews into next acquisition position and sleeps
# -- Stellarium satellite selection
#	- How this might work:
#		1. User selects satellite in stellarium, and slews to target
#		2. Python gets slew signal (timestamp, RA,DEC) and attempts to identify the 
#		   satellite by finding the closest object on its list to the user's target
#		3. Python sets this satellite as it's target and porceeds with #1 priority
# -- Feature Suggestion: PS3 Controller Related
#	 	1. Variable speed (ADDED 04/07/2015)
#	 		If user depressses certain buttons while using joysticks, changes slew
#			speed. Example: Fast - no buttons. Medium - R1. Fast - R2. 
#			This will be essential to fine-pointing.
# -- Alignment:
#		1. Need to add checks for the 3-star alignment procedure, send a couple
#			targets at different timestamps, see what Arduino returns with its
#			internal transformation
#		2. Need to validate the calibration method/configure Arduino to utilize
#			encoders
#	 
import sys
import re    # regex, used for str. repl., etc
import os    # for checking usb ports
import ephem
import ephem.stars
import urllib2
import math
import time
import struct
import stellariumConnect
import logging
import angles
import serial   # For arduino communication 
import struct   # for making binary packets to send to Arduino
import binascii # to see binary encodings in ascii -- debugging purposes
import pygame   # For joystick user input with PS3 controller

# Custom modules built for this project
import satellite
import satcom
import satinfo
import controller
import communicate
import keyboard
import telecoords

logging.basicConfig(level=logging.DEBUG)
# Switches:
connect   	   = 1 # enable stellarium connection
debug     	   = 1 # enable debugging
track     	   = 0 # enable satellite tracking
autotrack 	   = 0 # enable target acquisition
calibrateStars = 1 # enable star calibration

# Globals
uAz = 0.0
uAlt = 0.0
uAzLast = uAz
uAltLast = uAlt

def getTargetCoords(atTime):
	obs.date = time.strftime('%Y/%m/%d %H:%M:%S',time.gmtime(atTime))
	SAT.update(obs)
	return SAT.obj.az, SAT.obj.alt, atTime

# Finds 3 birghtest stars that meet these criteria:
#	1. Are bright/brightest
#	2. Are 22.5 degrees or more above the horizon
#	3. Are separated by at least 30 degrees in the sky
def setReferenceStars():
	starDBsize = len(ephem.stars.db.split("\n"))
	starDBnow = []
	starList = ephem.stars.db.split("\n")
	for i, star in enumerate(starList):
		if i < starDBsize-1:
			S = ephem.star(star.split(",")[0])
			S.compute(obs)
			if S.alt > math.pi/8: 
				starDBnow.append((S.name, S.alt, S.az, S.mag))

	starDBnow = sorted(starDBnow, key=lambda star: star[3])

	star1 = ephem.star(starDBnow[0][0])
	star1.compute(obs)

	star2 = None
	nxt = 1
	while nxt < len(starDBnow) and star2 == None:
		if abs(starDBnow[nxt][1] - star1.alt) > math.pi/8:
			azDiff = min(abs(starDBnow[nxt][2] - star1.az) % (2*math.pi),
					 2*math.pi - abs(starDBnow[nxt][2] - star1.az)  % (2*math.pi))
			if (azDiff > math.pi/6) and (abs(math.pi - azDiff) > math.pi/6):
				star2 = ephem.star(starDBnow[nxt][0])
		nxt = nxt + 1

	star2.compute(obs)
	star3 = None
	nxt = 1
	while nxt < len(starDBnow) and star3 == None:
		if ((abs(starDBnow[nxt][1] - star1.alt) > math.pi/8) or (abs(starDBnow[nxt][1] - star2.alt) > math.pi/8)):
			azDiff1 = min(abs(starDBnow[nxt][2] - star1.az) % (2*math.pi),
					 2*math.pi - abs(starDBnow[nxt][2] - star1.az)  % (2*math.pi))
			azDiff2 = min(abs(starDBnow[nxt][2] - star2.az) % (2*math.pi),
					 2*math.pi - abs(starDBnow[nxt][2] - star2.az)  % (2*math.pi))
			azDiff = min(azDiff1, azDiff2)
			if (azDiff > math.pi/6):
				star3 = ephem.star(starDBnow[nxt][0])
		nxt = nxt + 1

	star3.compute(obs)

	return star1, star2, star3

# function for testing encoder position reporting
def testCalibration():
	arduino.checkStatus()
	#arduino.resetOverrides()

	encoderFile = open('EncoderAltData2.csv','w')

	sign = 1
	altStop = 0
	while True:
		az1, alt1, tmp  = arduino.getCounts()
		azMotor1, altMotor1 = arduino.getMotors()
		#print('az: %d alt: %d alt_stop: %d' % (azS, altS, altStop))
		#print('azMotorS: %d, altMotorE: %d' % (azMotorS, altMotorS))

		arduino.goto(0, sign*1000) # alt, az

		sign = sign * -1; 

		time.sleep(10) # enough time to get off a stop

		az2, alt2, tmp  = arduino.getCounts()
		azMotor2, altMotor2 = arduino.getMotors()

		azDiff, altDiff           = (az2 - az1), (alt2 - alt1)
		azMotorDiff, altMotorDiff = (azMotor2 - azMotor1), (altMotor2 - altMotor1)

		print('az: %d, azE: %d, alt: %d, altE: %d, altDiff: %d' % (az1, az2, alt1, alt2, altDiff))
		print('altMotorS: %d, altMotorE: %d, altMotorDiff: %d' % (altMotor1, altMotor2, altMotorDiff))

		encoderFile.write('%d, %d, %d, %d\n' % (az1, az2, alt1, alt2))


#S.acquireTarget(arduino, az_t, alt_t, time_t)
#SAT = ephem.readtle(TLE[SELECTED],TLE[SELECTED+1],TLE[SELECTED+2])

obs = ephem.Observer();
obs.lat = '45.520'; # Coordinates for Portland, OR
obs.lon = '-122.682';
#obs.lat  = '33.433'; # Coordinates for Phoenix, AZ
#obs.lon = '-112.06';
obs.epoch = ephem.J2000;
obs.date = ephem.now()

# We need some information about our own star to determine satellite visibility :)
SUN = ephem.Sun() 
SUN.compute(obs)
print('SUN POSITION: AZ/ALT: %s / %s  | RA/DEC: %s / %s' % (ephem.degrees(SUN.az), ephem.degrees(SUN.alt), ephem.hours(SUN.ra), ephem.degrees(SUN.dec)))

# Acquire satellite information and initalize settings
satInfo = satinfo.satinfo(obs)
intercept = 0
if track or autotrack:
	TLEs 		= satInfo.acquireTLEs()
	magnitudes  = satInfo.acquireMagnitudes()

	satInfo.joinMagsAndTLEs() # correlate sat TLE data and magnitudes

	visible = satInfo.getBrightestVisible()
	print ('Current visible sats sorted by birghtness:')
	for vis in visible:
		print vis

	# Intercept code
	# 1. Identify target
	# 2. Compute intercept course
	# 3. Slew to target

	#target  = ephem.Jupiter()
	#target.compute(obs)
	target    = satInfo.getByName("SL-6 R/B")
	#target = visible[0][2]
	print(target.ra, target.dec)
	Ra_me, Dec_me = 0, 0  # where we are
	Ra_tg, Dec_tg = target.ra, target.dec  # where our target 

	SLmax  = math.radians(10) # deg/s
	SLtime = int(math.ceil(math.pi / SLmax)) # time to arc across the sky

	futureCoords = []
	interceps    = []
	print('Target: ', target)
	for seconds in range(SLtime):
		obs.date = ephem.Date(time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(seconds + time.mktime(time.gmtime()) - 60*60*8) ))
		target.compute(obs)
		Ra_tg, Dec_tg = float(target.ra), float(target.dec)

		travel        = [ (Ra_tg - Ra_me), (Dec_tg - Dec_me) ]   # rads to target pos at time +seconds
		travelMag     = math.sqrt( travel[0]**2 + travel[1]**2 ) # rads (dist) to same
		#travelSpd     = travelMag / 					     # rads/sec
		travelTime    = travelMag / SLmax
		interceptTime = travelTime - seconds # time differences between intercept position and target arrival -- minimize

		futureCoords.append([seconds, Ra_tg, Dec_tg, interceptTime]) # floats store ra, dec as radians
		print('{0} - RA: {1}, DEC: {2}, interceptTime: {3}'.format(seconds, ephem.degrees(target.ra), ephem.degrees(target.dec), interceptTime ))

	futureCoords.sort(key=lambda x : abs(x[3]))
	intercept = futureCoords[0]
	print intercept
	print('Out intercept is in {0}s at RA: {1} / DEC: {2} with diff: {3}s'.format(intercept[0], intercept[1], intercept[2], intercept[3]))

	SAT = satellite.satellite()
	SAT.setObj(target)
	SAT.setObs(obs)

	# User input for satellite selection
	#uInput = raw_input()
	#uSat = int(uInput)
	#uSat = 0

	#SELECTED = uSat*3

	#Print Space station TLE data
	#for i in range(SELECTED,SELECTED+3):
	#	print(TLE[i])


	AltOld = 0.0
	AzOld  = 0.0

dt = 0.2
spd   = 0.20 # rad/s, max speed for user input
spdMin = 0.005
ps3speed = 0
keySpeed = 1000
# Joystick speed multipliers 
spdSlow = 50
spdMed  = 200
spdFast = 500
nStar   = 0
nStarLast = -1
refStars = []

tCoords = telecoords.telecoords()
# DELETE -- Just for testing
if False:
	for nStar in range(3):
		if len(refStars) == 0:
			refStars = setReferenceStars()
		if nStarLast != nStar:
			print('Ref Star %d, %s' % (nStar, refStars[nStar].name))
			nStarLast = nStar

		obs.date = ephem.now()
		refStars[nStar].compute(obs)
		Ra_t, Dec_t = float(refStars[nStar].ra), float(refStars[nStar].dec)

		tCoords.addStar(refStars[nStar], obs, Ra_t, Dec_t)
		nStar = (nStar + 1) % 3

		time.sleep(60)

	print tCoords.T

# Set up keyboard handling
pygame.display.init()
pygame.display.set_mode((300,300))
KB = keyboard.keyboard(pygame)
KB.setSpeeds(dt, spdMin, spd) # speed range for keyboard input

# Main code
if __name__ == '__main__':
	try:
		# Check for a PS3 controller connected
		pygame.init()
		if pygame.joystick.init(): # Suspect, seems to return false even when joystick is present
			if pygame.joystick.Joystick(0):
				joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
		else:
			joysticks = []

		print joysticks

		ps3 = controller.controller()
		ps3sw = False

		if ps3.getJoystick(joysticks):
			print("Joystick Detected")
			print("Calibrating Joystick...")
			ps3.calibrate()
			print("Calibration Done.")
			ps3sw = True
		else:
			print("Joystick Not Detected")

		# Establish Arduino communication
		arduino = communicate.communicate()
		
		if arduino.port:
			print("Arduino port: %s\n" % arduino.port)
		else:
			print("Arduino not detected.\n")

		# Establish stellarium communication
		if connect:
			sCon = stellariumConnect.stellariumConnect('localhost',10001)
			sCon.handshakeStellarium()

		if track:
			S = satcom.satcom()
			
			# Future time
			az_t = [0, 0, 0]
			alt_t = [0, 0, 0]
			time_t = [0, 0, 0]
			#for i in range(3):
			#	nextTime = time.mktime(time.gmtime()) + i
			#	az_t[i], alt_t[i], time_t[i] = getTargetCoords(nextTime)
			#	time_t[i] = (time_t[i] - presentTime) * 1000

			#deltaTime = firstPass[0] - time.mktime(time.gmtime())
			#print(deltaTime)

		if arduino.port: ## testing some calibration code
			testCalibration()
		
		while True:
			#obs.date = ephem.Date(time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(60*30 + time.mktime(time.gmtime())) )) # setting time for debugging
			obs.date = ephem.now()	
			#print ('Date: %s' % (format(obs.date)))
			if intercept:
				SAT.update(obs)

				Ra_tg  = intercept[1]
				Dec_tg = intercept[2]
				
				route      = [ (Ra_tg - Ra_me), (Dec_tg - Dec_me) ]
				routeMag   = math.sqrt( route[0]**2 + route[1]**2 )

				routeNorm  = [ route[0] / routeMag, route[1] / routeMag ] if routeMag > 0 else [0, 0]

				if ( routeMag / dt ) < SLmax:
					slew = [ route[0] / dt, route[1] / dt ]
					step = route
					intercept = 0
					track     = 1
				else:
					slew = [ routeNorm[0] * SLmax, routeNorm[1] * SLmax ]
					step = [ slew[0] * dt, slew[1] * dt ]

				Ra_me  = Ra_me  + step[0]
				Dec_me = Dec_me + step[1]

				print('Me: [%3.2f, %3.2f], Targ: [ %3.2f, %3.2f ] deg. Slew: [%3.2f, %3.2f] deg/s. Slew step: [%3.2f, %3.2f]' \
														% (math.degrees(Ra_me),    math.degrees(Dec_me),
														   math.degrees(Ra_tg),    math.degrees(Dec_tg), 
														   math.degrees(slew[0]),  math.degrees(slew[1]),
														   math.degrees(step[0]),  math.degrees(step[1]) ) )

			if track:
				SAT.update(obs)

				Ra =  angles.Angle(r=SAT.obj.ra)
				Dec = angles.Angle(r=SAT.obj.dec)
				Alt = math.degrees(SAT.obj.alt)
				Az  = math.degrees(SAT.obj.az)

				Ra.ounits  = "hours"
				Dec.ounits = "degrees"

				slewSpeed = [(Az-AzOld), (Alt-AltOld)]

				if (slewSpeed[0] != 0) & (slewSpeed[1] != 0):
					visible = 'VISIBLE' if SAT.check_pass(0) else 'NOT VISIBLE'
					#visible = 'NOT VISIBLE'
					up = 'UP' if (Alt > 0.0) else 'NOT UP'
					print('AZ/ALT: %f / %f  | RA/DEC: %s / %s | SLEW: %f / %f (deg/s) -- %s, %s' % (Az, Alt, Ra, Dec, slewSpeed[0], slewSpeed[1], up, visible))
					#print('AZ/ALT: %f / %f  | RA/DEC: %s / %s | SLEW: %f / %f (deg/s) -- %s, %s' % (Az, Alt, ephem.hours(SAT.obj.ra), ephem.degrees(SAT.obj.dec), slewSpeed[0], slewSpeed[1], up, visible))

				AltOld = Alt
				AzOld  = Az

			# Handle joystick input
			if ps3sw:
				ps3.updateAxis()

				# Handle PS3 joystick speed settings
				if ps3.getR1():
					ps3speed = spdSlow
				elif ps3.getL1():
					ps3speed = spdMed
				else:
					ps3speed = spdFast

				azStick  = ps3.left[0]  - ps3.cL[0]
				altStick = ps3.right[1] - ps3.cR[1]
				# Joystick deadzones
				if (abs(azStick) < 0.1):
					azStick = 0.0
				if (abs(altStick) < 0.1):
					altStick = 0.0
				uAz = uAz + (spd*azStick*dt)*0.5
				uAlt = uAlt + (spd*altStick*dt)*0.5
				logging.debug("User pos: %f / %f " % (uAz, uAlt))
				logging.debug("PS3-left/right: %f / %f " % (azStick, altStick))

			# Keyboard input allowed at any time
			mAz, mAlt = KB.getArrowMoves() 
			uAz, uAlt = uAz + mAz, uAlt + mAlt

			# do 3-star calibration
			if calibrateStars and not tCoords.ready:
				if len(refStars) == 0:
					refStars = setReferenceStars()
				if nStarLast != nStar:
					print('Ref Star %d, %s' % (nStar, refStars[nStar].name))
					nStarLast = nStar

				Ra_t, Dec_t = obs.radec_of(uAz, uAlt)

				if KB.getEnter():
					obs.date = ephem.now()
					tCoords.addStar(refStars[nStar], obs, Ra_t, Dec_t)
					nStar = (nStar + 1) % 3


			# Send data to Arduino
			if arduino.port:
				#nextTime = time.mktime(time.gmtime()) + 1 # 1 second from now
				#az_t, alt_t, time_t = getTargetCoords(nextTime)
				#time_t = (time_t - presentTime)*1000
				#S.updateTarget(arduino, az_t, alt_t, time_t)
				#arduino.swrite("chck")
				#arduino.checkDone()
				#print('Pointing to: %f / %f' % (S.alt_m, S.az_m))
				#logging.debug('Sending %d / %d' % (ps3speed*uAz, ps3speed*uAlt))
				if (mAz != 0 or mAlt != 0):
					arduino.goto(keySpeed * mAz, keySpeed * mAlt);
					az, alt, altStop = arduino.getCounts()
					print('Actual pos (cnts): az: %d alt: %d stop: %d' % (az, alt, altStop))
				#arduino.goto(ps3speed*azStick, ps3speed*altStick)

			# Send data to stellarium
			if connect and not track and not intercept:
				Ra_m, Dec_m = obs.radec_of(uAz, uAlt)
				uRa  = angles.Angle(r=Ra_m)
				uDec = angles.Angle(r=Dec_m)
				sCon.sendStellariumCoords(uRa, uDec)
			elif connect and intercept:
				Ra  = angles.Angle(r=Ra_me)
				Dec = angles.Angle(r=Dec_me)
				sCon.sendStellariumCoords(Ra, Dec)
			elif connect and track:
				#Ra_m, Dec_m = obs.radec_of(Az, Alt)
				#Ra.r  = Ra_m
				#Dec.r = Dec_m
				sCon.sendStellariumCoords(Ra, Dec)
				

			time.sleep(dt)
			
	except KeyboardInterrupt:
		logging.debug("\nBye!")

# END WORKING CODE

