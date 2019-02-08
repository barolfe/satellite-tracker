
# Class to communicate with Stellarium
import os
import serial
import logging
import struct
import binascii # to see binary encodings in ascii -- debugging purposes

logger = logging.getLogger(__name__)

class stellarium:
	def __init__(self):
		self.port = False
		self.checkArduino();
		if self.port:
			self.connect(self.port)

	def connect(self, usb_serial="/dev/tty.usbmodem1421", usb_serial_baud=115200, timeout=2):
		self.serial = serial.Serial(usb_serial, usb_serial_baud, timeout=timeout)
		if self.swrite("test"):
			print("Connection Established\n")
		else:
			print("Connection Failed\n")

	def disconnect(self):
		self.serial.close()
		return True

	def sread(self):
		line = self.serial.readline().rstrip()
		return line

	def checkArduino(self):
		if os.path.exists("/dev/tty.usbmodem1421"):
			self.port = "/dev/tty.usbmodem1421"
		elif os.path.exists("/dev/tty.usbmodem1411"):
			self.port = "/dev/tty.usbmodem1411"
		else:
			return False

	def checkDone(self):
		resp = self.sread()
		logging.debug(resp)
		while (resp != 'done'):
			resp = self.sread()
			logging.debug(resp)
		if (resp=='done'):
			return True
		else:
			return False

	def checkStatus(self, cmd):
		resp = self.sread()
		logging.debug(resp)
		while (resp != cmd):
			resp = self.sread()
			logging.debug(resp)

	def goto(self, az, alt):
		self.swrite("move")
		logging.debug('test')
		self.swriteInt(az)
		self.swriteInt(alt)
		self.checkDone()

	def swrite(self,cmd):
		self.serial.write(cmd)
		return self.checkDone()

	def swriteFloat(self, val):
		self.checkStatus('float')
		val_a = struct.pack("<f", val)
		logging.debug("Sending float %f as 4-byte string: %s" % (val, binascii.hexlify(val_a)))
		self.serial.write(val_a)
		self.checkDone()

		# Verify the value
		logging.debug("Readback: %s" % self.sread())

	def swriteInt(self, val):
		self.checkStatus('int')
		val_a = struct.pack("i", val)
		logging.debug("Sending int %f as 4-byte string: %s" % (val, binascii.hexlify(val_a)))
		self.serial.write(val_a)
		self.checkDone()

		# Verify the value
		logging.debug("Readback: %s" % self.sread())