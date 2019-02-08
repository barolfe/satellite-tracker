import numpy as np
import ephem
import math 

# TODO: Check that angle calcs. are consistent with Ra/Dec system (especially negative angles and such)

# Provides utilities to compute/determine coordinate transforms based on reference stars
#   provided by the caller. 
# Provides functions to perform theese coordinate transforms once the transform is computed

# | l |   | T11 T12 T13 | | L |         | L |
# | m | = | T21 T22 T23 | | M | = [ T ] | M |
# | n |   | T31 T32 T33 | | N |         | N |

# | l |   |math.cos(theta) *math.cos(phi) |
# | m | = |math.cos(theta) * sin(phi) |
# | n |   |        sin(theta)     |

# | L |   |math.cos(delta) *math.cos(alpha - k * (t - t0)) |
# | M | = |math.cos(delta) * sin(alpha - k * (t - t0)) |
# | N |   |              sin(delta)                |

# theta, phi   = dec, ra observed
# delta, alpha = dec, ra true
# t0           = observation time

# __init__():                         Initializer. 
# computeTransform()                  Compute the coordinate transform matrix [T] (if possible)

# APIs 
# addStar(starObj, observer):         Add a reference star (ephem obj) and an observer at the time it was observed (observer)
# computeTelescopeRaDec(Ra, Dec):     Pass true Ra,Dec of object in radians, returns telescope Ra, Dec
# computeTelescopeAltAzPass(Alt, Az): Pass true Alt, Az, returns telescope Alt, Az -- this will wrap around the above

class telecoords:
    def __init__(self):
        self.l = np.array( [ [1, 0, 0], [ 0, 1, 0], [0, 0, 1] ], np.float ) # telescope coordinates
        self.L = np.array( [ [1, 0, 0], [ 0, 1, 0], [0, 0, 1] ], np.float ) # true coordinates
        self.T = self.L # coordinate transform

        self.nStar = 0 # number of stars added
        self.k  = 1.002737908 # Constant.. Relationship between the solar time (M) and the sidereal time (S): (S = M * 1.002737908)
        self.t0 = 0
        self.enoughStars = False
        self.ready = False

    # add a reference star (ephem obj) observed at obs (ephem observer) w/ tele coords theta, phi
    def addStar(self, star, obs, ra, dec):
        n = self.nStar
        star.compute(obs)
        theta, phi   = dec, ra
        delta, alpha = float(star.dec), float(star.ra)
        t = self.dayToRad(float(obs.date)) # obs.date = days from J2000 (w/ 1 second precision, I believe)

        # set reference time if first star
        if n == 0:
            self.t0 = t

        # add columns to our coordinate matrices
        self.l[:, n] = self.eqToCart(theta, phi)
        self.L[:, n] = self.eqToCart(delta, alpha - self.k * (t - self.t0)) 

        self.nStar = (self.nStar + 1) % 3

        if self.nStar == 2:
            self.enoughStars = True
        if self.nStar == 0:
            self.computeTransform()

    def makeThirdStar(self):
        # third star can be created by taking the cross product of our other two stars, and normalizing for a mag. 1
        if not self.nStar == 2:
            print('Need 2 stars to compute a third star')
            return

        point = np.cross( self.l[:, 0], self.l[:, 1])
        point = point / np.linalg.norm(point)

        star = np.cross( self.L[:, 0], self.L[:, 1])
        star = star / np.linalg.norm(star)

        self.l[:, 2] = point
        self.L[:, 2] = star

    def dayToRad(self, day):
        return 2 * math.pi * day

    def matInv(self, M):
        return np.linalg.inv(M)

    def eqToCart(self, theta, phi):
        l = math.cos(theta) * math.cos(phi)
        m = math.cos(theta) * math.sin(phi)
        n = math.sin(theta)
        return [l, m, n]

    def cartToEq(self, l):
        x, y, z = l[0], l[1], l[2]
        phi   = math.atan2(y, x) # result is between -pi and pi
        theta = math.asin(z)     # between -pi/2 and pi/2

        return theta, phi

    def computeTransform(self):
        if not self.enoughStars:
            print('Need at least 2 reference stars before transform can be computed.')
            return

        if self.nStar == 2:
            # make a third star, since only 2 were provided
            self.makeThirdStar()

        Linv   = self.matInv(self.L)   # matrix inverse of L (thank you numpy)
        self.T = np.dot( self.l, Linv ) # it's that easy.

        # sanity check on inverse
        print np.dot(self.L, Linv)

        self.ready = True

    def computeTelescopeRaDec(self, Ra_true, Dec_true, obs):
        if not self.ready:
            print('Warning: Transform has not been computed. Returning trivial transformation (identity)')
        
        t   = float(obs.date)
        ra  = Ra_true - self.k * (t - self.t0)
        dec = Dec_true 

        L = self.eqToCart(dec, ra) # polar to cartesian 
        l = np.dot( self.T, L ) # perform transform

        theta, phi = self.cartToEq(l) # convert back to polar coordinates







