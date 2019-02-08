# Handle the mechanical aspects -- the gotos require routing
# Mechanics are Alt-Az, so if passing Az-Dec, we need to take this into consideration
# The no-go zone has two purposes:
#   1. It addresses the non-contunious encoder strip I'm using (there'll be a point 
#       where the two ends join)
#   2. It'll prevent the tracker from wrapping the cables (rotating more than 360 
#       total in any direction)
#
# Important questions:
#   1. How does the existence of the no-go zone affect calibration? 
#      We'd have to make assumptions re. the flipped coordinates/econders
#   2. How should the no-go zone be treated when slewing manually? 
#      An automated flip procedure could occur, but this might make the user
#      experience less than ideal...
#   
# Altitude is generally constrained between 0 and 90 degrees, but in reality,
#   we can exploit 0-180 degrees. Thus, every point has a degenercy of 2.
#   1. Alt/Az - normal
#   2. 180 - Alt, 180 + Az -- flipped
#
# Every path can also be described without having to execute a flip mid-way.
#
#   - If known a priori, the entire route should be checked. If a flip will occur, then routing
#     should be calculated to avoid any mid-track flips
#
# There are two conditions in which the no-go zone might be encounterd
#   1. If alt <=90, and theta_1 < az < theta_2
#   2. If alt > 90, and theta_1 < az +/- 180 < theta_2

# theta_s = start azimuth
# theta_e = end   azimuth
# theta_1 = start D.N.C.
# theta_2 = end   D.N.C.

# (all angle differences modulo 180)
# | theta_s - theta_e | <= 180 (necessary)
#
# if ( | theta_s - theta_2 |  > | theta_e - theta_2 | ):
#   then:
#        (theta_s > theta_2 > theta_1 > theta_e
#       if ( | theta_s - theta_2 | + | theta_e - theta_1| ) < 180:
#           Path crosses D.N.C., use flipped coordinates 
#   else:
#        (theta_e > theta_2 > theta_1 > theta_s)
#        Same check, swap theta_e/theta_s for check
#       

import math

class mechanical():

    def __init__(self):
        self.noGo  = [0, math.pi*5/180] # 5 degree zone we can't access
        self.flip  = False
        self.SLmax = 10

    def setMaxSpeed(self, spd):
        self.SLmax = spd

    # return alt, az, if az were rotated 180
    def getFlipped(self, alt, az):
        az_new  = (az + math.pi)  % math.pi
        alt_new = (math.pi - alt)
        return az_new, alt_new

    # Check if route passes a no-go zone
    def checkRoute(self, az_me, route):
        chk = [az_me, route[0], az_me + route[0]]
        if chk[0] < self.noGo[0] and chk[1] > 0 and chk[2] > self.noGo[1]:
            return False
        if chk[0] > self.noGo[1] and chk[1] < 0 and chk[2] < self.noGo[0]: # CHECK
            return False

        return True

    # Keep between 0 and 2*pi
    def constrain(self, az, alt):
        return az % (2 * math.pi), alt % (2* math.pi)

    # Determine the mechanical route to a target
    def findRoute(self, az_me, alt_me, az, alt):
        self.flip = False
        # Check if in no-go zone, we'll have to use coordinates rotated 180
        if alt > self.noGo[0] and alt <= self.noGo[1]
            self.flip = True
            alt, az   = getFlipped(alt, az)

        route      = [ (az - az_me), (alt - alt_me) ]

        # Check if route passes the no-go zone
        if not self.checkRoute(az_me, route):
            route = [ (-route[0]/abs(route[0]) ) * (2*math.pi - route[0]),  ]
        routeMag   = math.sqrt( route[0]**2 + route[1]**2 )

        routeNorm  = [ route[0] / routeMag, route[1] / routeMag ] if routeMag > 0 else [0, 0]

        if ( routeMag / dt ) < self.SLmax:
            slew = [ route[0] / dt, route[1] / dt ]
            step = route
            intercept = 0
            track     = 1
        else:
            slew = [ routeNorm[0] * self.SLmax, routeNorm[1] * self.SLmax ]
            step = [ slew[0] * dt, slew[1] * dt ]

        az_me  = az_me  + step[0]
        alt_me = alt_me + step[1]