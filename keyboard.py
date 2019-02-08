import pygame
import logging
import time

class keyboard:
    def __init__(self, pygameObj):
        self.pygame = pygameObj
        self.arrowLast = [0,0]
        self.arrowTimeDown = [0,0]
        self.timeLast = time.time()
        self.spdMin = 0
        self.spdMAx = 0
        self.dt     = 1

    def getEnter(self):
        keyState = self.pygame.key.get_pressed()
        self.pygame.event.pump()
        if keyState[self.pygame.K_RETURN]:
            return True
        else:
            return False

    def getArrowInput(self):
        timeElapsed = time.time() - self.timeLast

        keyMovement = [0, 0] # L/R, U/D
        keyState = self.pygame.key.get_pressed()
        if keyState[self.pygame.K_DOWN]:
            keyMovement[1] = -1
        if keyState[self.pygame.K_UP]:
            keyMovement[1] = 1
        if keyState[self.pygame.K_LEFT]:
            keyMovement[0] = -1
        if keyState[self.pygame.K_RIGHT]:
            keyMovement[0] = 1

        for i in range(2):
            if keyMovement[i] == self.arrowLast[i]:
                self.arrowTimeDown[i] = self.arrowTimeDown[i] + timeElapsed
            else:
                self.arrowTimeDown[i] = 0

        self.arrowLast = keyMovement

        self.pygame.event.pump()
        return keyMovement, self.arrowTimeDown

    def getArrowMoves(self):
        mAz, mAlt = 0, 0
        keyMoves, keyTimeDown = self.getArrowInput()
        keySpd = [0, 0]
        keySpd[0] = (keyTimeDown[0]/100) * self.spdMax if ( (keyTimeDown[0]/100) * self.spdMax < self.spdMax ) else self.spdMax
        keySpd[1] = (keyTimeDown[1]/100) * self.spdMax if ( (keyTimeDown[1]/100) * self.spdMax < self.spdMax ) else self.spdMax
        keySpd[0] = keySpd[0] if keySpd[0] > self.spdMin else self.spdMin
        keySpd[1] = keySpd[1] if keySpd[1] > self.spdMin else self.spdMin

        if keyMoves[0] or keyMoves[1]:
            mAlt  =  (keySpd[0] * self.dt * keyMoves[0])
            mAz =  (keySpd[1] * self.dt * keyMoves[1])
            print(mAz, mAlt)

        return mAz, mAlt

    def setSpeeds(self, dt, spdMin, spdMax):
        self.dt     = dt
        self.spdMin = spdMin
        self.spdMax = spdMax