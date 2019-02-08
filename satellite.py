# satellite module, wraps pyephem and provudes some utilities
import ephem
import logging
import math
logger = logging.getLogger(__name__)

class satellite:
    def __init__(self, TLE=None, obs=None):
        # TLE should be an array; each element holding one line
        if TLE is not None:
            self.obj = ephem.readtle(TLE[0], TLE[1], TLE[2])
        if obs is not None:
            self.OBS = obs
        self.SUN = ephem.Sun() 

    def setObj(self, obj):
        self.obj = obj
    def setObs(self, obs):
        self.obs = obs
    def printPos(self):
        print( '... {0} -- {1} / {2}'.format(self.obs.date, math.degrees(self.obj.alt), math.degrees(self.obj.az)) )
    def update(self, obs):
        self.obs = obs
        self.obj.compute(obs)

    def check_pass(self, passTime):
        if passTime == 0:
            self.OBS.date = ephem.now()
        elif passTime == 1:
            pass
        else:
            timeStr = time.strftime('%Y/%m/%d %H:%M:%S',time.gmtime(passTime)) # UTC time string needed for ephem
            self.OBS.date = ephem.Date(timeStr)
        
        self.obj.update(self.OBS)
        self.SUN.compute(self.OBS)

        if (self.obj.alt > 0.175) & (self.SUN.alt < -0.1) & (not self.obj.eclipsed):      # 0.175 = 10 degrees, 0.1 = 6 degrees        return True
            return True
        else:
            return False

    def search_visible(self, tStart, tIncr, tEnd):
        passes = []
        futureTime = tStart
        
        while futureTime <= tEnd:
            futureTime = futureTime + tIncr     
            if check_pass(futureTime):
                passes.append(futureTime)

        return passes

    def unique_visible(self, passes, tIncr):
        unique = []
        for i in range(len(passes)-1):
            if abs(passes[i] - passes[i+1]) < 2 * tIncr:    # Identical pass?
                pass
            else:
                unique.append(passes[i])                    # Unique pass

        return unique

    def refine_visible(self, passes, tIncr):
        refined = list()
        for passTime in passes:
            refinedPasses = search_visible(passTime - 5 * 60, tIncr, passTime + 5*60)       # Look forward/backward 5 minutes
            refined.append(refinedPasses)

        return refined
