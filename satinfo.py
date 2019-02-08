import re
import os
import urllib2
import struct
import ephem


class satinfo():

    def __init__(self, obs):
        self.obs        = obs
        self.TLEs       = [] 
        self.satObjs    = []
        self.magnitudes = {}
        self.meta    = []

    def acquireTLEs(self, url="http://www.celestrak.com/NORAD/elements/visual.txt"):
        if os.path.isfile('TLE.txt'):
            with open('TLE.txt') as tleFile:
                rawTLE = tleFile.read()
        else:
            rawTLE = urllib2.urlopen(url).read()
            with open('TLE.txt','w') as tleFile:
                tleFile.write(rawTLE)

        TLE = rawTLE.splitlines()

        self.TLEs    = []
        self.satObjs = []

        for i, l in enumerate(TLE):
            if ((i % 3) == 0):
                self.TLEs.append( TLE[i:i+3] )
                TLELineSplit = TLE[i+1].split()
                satID        = TLELineSplit[2].strip()
                satTmp       = ephem.readtle(TLE[i],TLE[i+1],TLE[i+2])
                satTmp.compute(self.obs)
                up = 'UP' if (satTmp.alt > 0.175) else 'NOT UP'
                try: 
                    visInfo = self.obs.next_pass(satTmp)
                except:
                    visInfo = ['NEVER']
                print('%d. - %s -- %s, Next: %s' % ((i/3),TLE[i], up, visInfo[0]))
                self.satObjs.append([satID,satTmp])

        return self.TLEs

    def acquireMagnitudes(self, fileName='qs.mag'):
        # Get information about magnitudes
        fieldwidths = (6,2,10,15,5) # entry num, d, designation, name, mag.
        lenReq      = sum(fieldwidths) # required line length
        fmtstring   = ' '.join('{}{}'.format(abs(fw), 'x' if fw < 0 else 's') for fw in fieldwidths)
        fieldstruct = struct.Struct(fmtstring)
        parse       = fieldstruct.unpack_from

        with open(fileName) as magFile:
            line = magFile.readline() # ignore header line
            for line in magFile:
                if (len(line) < lenReq) or ('Comments' in line):
                    pass
                else:
                    lineList = parse(line)
                    desig    = re.sub(r'(?<=\d)\s(?=\d)', '0', lineList[2]) # replace middle space with 0 67 685A becomes 670685A
                    desig    = desig.strip() # remove whitespace
                    self.magnitudes[desig] = float(lineList[4]) if not (lineList[4].strip() == '') else 99

        return self.magnitudes

    def getVisible(self):
        visible = []
        if len(self.satObjs) == 0:
            print('satObjs empty')
            return
        else:
            for i, [satID, obj] in enumerate(self.satObjs):
                obj.compute(self.obs)
                if obj.alt > 0.175:
                    visible.append([i, satID, obj])

        return visible

    def getBrightestVisible(self):
        if len(self.meta) == 0:
            print('No brightness information available... maybe you need to call joinMagsAndTLEs?')
            return

        visible        = self.getVisible()
        visibleSats    = []
        if len(visible) == 0:
            print('No satellites above the horizon right now.')
            visibleSats.append( [ 0, self.satObjs[0][0], self.satObjs[0][1], self.meta[self.satObjs[0][1]] ] )
            return
        else:
            for vis in visible:
                iSat = vis[0]
                visibleSats.append([ vis[0], vis[1], vis[2], self.meta[iSat][2] ])

        visibleSats.sort(key=lambda sat: sat[3])
        return visibleSats

    def getByName(self, name):
        if len(self.meta) == 0:
            print('No meta data available. Run joinMagsAndTLEs first.')
            return

        for i, sat in enumerate(self.meta):
            if name in sat[3]:
                return self.satObjs[i][1]

        return None
    
    def getISS(self):
        return self.getByName("ISS")

    def joinMagsAndTLEs(self):
        error = False
        if not self.TLEs:
            print "TLE data is empty, cannot join."
            error = True
        if not self.magnitudes:
            print "magnitudes data is empty, cannot join."
            error = True
        if error:
            return
        for i,tle in enumerate(self.TLEs):
            TLELineSplit = tle[1].split()
            satID        = TLELineSplit[2].strip()
            satName      = tle[0]
            if (satID in self.magnitudes):
                mag          = self.magnitudes[satID]
            else:
                mag = 99
            self.meta.append( [i, satID, mag, satName] )

    def updateObs(self, obs):
        self.obs = obs

