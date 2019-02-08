# Class to handle the PS3 controller input
import pygame
import time
import logging
logger = logging.getLogger(__name__)
class controller:
	def __init__(self):
		self.joystick = None
		self.left = [0,0]
		self.right = [0,0]
		self.cL = [0, 0]
		self.cR = [0, 0]
		pygame.init()

	def calibrate(self):
		L = [0,0]
		R = [0,0]
		for i in range(10):
			self.updateAxis()
			L[0] += self.left[0]
			L[1] += self.left[1]
			R[0] += self.right[0]
			R[1] += self.right[1]
		self.cL = [L[0]/10.0, L[1]/10.0]
		self.cR = [R[0]/10.0, R[1]/10.0]

    # Key Ref: 0 = select;  2 = R3; 3 = start; 5 = right arrow; 7 = left arrow;
    #		   4 = up; 9 = R2; 12 = triangle; 13 = circle; 14 = X; 

	def getR1(self):
		if self.joystick:
			return self.joystick.get_button(11) #R1
		else:
			return False

	def getL1(self):
		if self.joystick:
			return self.joystick.get_button(10) #R1
		else:
			return False

	def getX(self):
		if self.joystick:
			self.update()
			return self.joystick.get_button(14)
		else:
			return False

	def getJoystick(self, joysticks):
		for joystick in joysticks:
			if 'playstation' in joystick.get_name().lower():
				logging.debug(joystick.get_name())
				self.joystick = joystick
				self.joystick.init()
				return True

		return False

 	def waitUntilPressed(self, button):
 		if button == 'X':
 			while self.getX() != True:
 				time.sleep(0.1)

	def update(self):
		pygame.event.pump()

	def updateAxis(self):
		if self.joystick is not None:
			try:
				self.update()
				self.left = [self.joystick.get_axis(0) - self.cL[0], self.joystick.get_axis(1) - self.cL[1]]
				self.right =[ self.joystick.get_axis(2) - self.cR[0], self.joystick.get_axis(3) - self.cR[1]]
			except pygame.error:  
				print("Axis Error")