# A class to communicate with arduino
import ephem
import logging
logger = logging.getLogger(__name__)
class satcom:
	# Function that will send laser state (integer value 0 = off, 1-255 = intensity)
	def __init__(self):
		self._calib = False
		self._star_n = 0
		self._t0 = 0.0

	def lase(self, comm, val):
		comm.swrite("lase")
		comm.swriteInt(val)

	def acquireTarget(self, comm, az, alt, t):
		comm.swrite("ntgt")
		for i in range(3):
			comm.swriteFloat(az[i])
		for i in range(3):
			comm.swriteFloat(alt[i])
		for i in range(3):
			comm.swriteInt(t[i])
		arduino.checkDone()

	def updateTarget(self, comm, az, alt, t):
		comm.swrite("utgt")
		comm.swriteFloat(az)
		comm.swriteFloat(alt)
		comm.swriteInt(t)
		arduino.checkDone()

	def update(self, comm, az, alt):
		comm.swrite('satg') # will get a done msg, then a float msg
		# Ready for the floats, let's send them
		comm.swriteFloat(az)
		comm.swriteFloat(alt)
		comm.checkDone()

	def readPos(self, comm):
		comm.swrite('gpos')
		comm.checkStatus('float')
		self.az_m = float(comm.sread())
		comm.checkStatus('float')
		self.alt_m = float(comm.sread())
		comm.checkDone()

    # Send reference stars to Arduino board
	def sendStar(self, comm, star, obs):
		comm.swrite('sndS')
		comm.swriteInt(self._star_n) # Reference #
		# Next we'll send the star's Ra and Dec in radians
		obs.date = ephem.now() # PyEphem stores dates as floating point values 
							   # relative to # days since the last day of 1899 @ noon
		if self._star_n == 0:
			self._t0 = obs.date
		star.compute(obs)
		comm.swriteFloat(star.ra)
		comm.swriteFloat(star.dec)
		comm.swriteFloat(star.az)
		comm.swriteFloat(star.alt)
		comm.swriteFloat(obs.date-self._t0)
		comm.checkDone()
		self._star_n = self._star_n + 1
