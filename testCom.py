#!/usr/bin/python

import communicate as com
import time

while True:
	a = com.communicate()
	az, alt = a.getCounts()
	
	print(az, alt)
	time.sleep(1)
