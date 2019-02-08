    # Initialize a PyEphem object
    #SAT = ephem.readtle(TLE[SELECTED],TLE[SELECTED+1],TLE[SELECTED+2])
    userSat = 0 # disabled for now
    if userSat:
        obs.date = ephem.now()
        SAT = satellite.satellite(TLE[SELECTED:SELECTED+3], obs)
        SAT.update(obs)
        SAT.printPos()
        #print('%s Information:' % TLE[SELECTED])

        # Determine when the next visible pass will occur
        presentTime = time.mktime(time.gmtime())
        futureTime = presentTime

        visible = search_visible( presentTime, 60 * 2, presentTime + 10 * 24 * 60 * 60)
        visible = unique_visible(visible, 60 * 5)

        passes = refine_visible(visible, 1) # List of a list of passes.

        print('Visible passes for the next 10 days at %s, %s' % (obs.lat, obs.lon))
        print('(all times are UTC)')
        for singlePass in passes:
            #maxAlt = find_highest(singlePass)
            print( 'Start: {0}'.format(time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(singlePass[0]) ) ) ) 
            print( 'End:   {0}'.format(time.strftime( '%Y/%m/%d %H:%M:%S', time.gmtime(singlePass[ len(singlePass) - 1 ]) ) ) )

        # Pick single pass and explore data
        firstPass = passes[0]

        if debug:
            print('Example of pass -- current time: {0}'.format(time.gmtime(ephem.now())))
            for point in firstPass:
                #print point
                timeStr = time.strftime('%Y/%m/%d %H:%M:%S',time.gmtime(point)) # UTC time string needed for ephem
                obs.date = ephem.Date(timeStr)
                SAT.update(obs)
                SAT.printPos()

# This function doesn't work at the moment
def find_highest(singlePass):
    maxAlt = 0.0
    for i in range(len(singlePass)):
        obs.date = singlePass[i]
        SAT.update(obs)
        if maxAlt > SAT.obj.alt:
            maxAlt = SAT.obj.alt
    return maxAlt
def check_pass(passTime):
    if passTime == 0:
        obs.date = ephem.now()
    elif passTime == 1:
        pass
    else:
        timeStr = time.strftime('%Y/%m/%d %H:%M:%S',time.gmtime(passTime)) # UTC time string needed for ephem
        obs.date = ephem.Date(timeStr)
    
    SAT.update(obs)
    SUN.compute(obs)

    if (SAT.obj.alt > 0.175) & (SUN.alt < -0.1) & (not SAT.obj.eclipsed):      # 0.175 = 10 degrees, 0.1 = 6 degrees        return True
        return True
    else:
        return False

def search_visible(tStart, tIncr, tEnd):
    passes = []
    futureTime = tStart
    
    while futureTime <= tEnd:
        futureTime = futureTime + tIncr     
        if check_pass(futureTime):
            passes.append(futureTime)

    return passes

def unique_visible(passes, tIncr):
    unique = []
    for i in range(len(passes)-1):
        if abs(passes[i] - passes[i+1]) < 2 * tIncr:    # Identical pass?
            pass
        else:
            unique.append(passes[i])                    # Unique pass

    return unique

def refine_visible(passes, tIncr):
    refined = list()
    for passTime in passes:
        refinedPasses = search_visible(passTime - 5 * 60, tIncr, passTime + 5*60)       # Look forward/backward 5 minutes
        refined.append(refinedPasses)

    return refined
