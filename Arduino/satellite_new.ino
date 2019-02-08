// Testing a new serial protocol for python/arduino communication
//   before, arduino would wait for a command from python before doing
//   anything else, where what I actually want is for arduino to do 
//   what it needs to do, and when it has a chance, check for a pending
//   command. If there is incoming serial data, it will read it, and let
//   the Python code know it's ready to receive additional data.
//   Arduino dictates the terms of the conversation.

//  Easy driver AZ-axis: ~6200 1/8th steps = 90 degrees
//    Slip ~50 1/8th steps 
//    ~68.9 steps/degree
//  EASY DRIVER ALT-axis ~2400 1/8th steps = 90 degrees
//    Slip ~15 1/8th steps
//    ~26.7 steps/degree

//  Types of coordinates:
//   1. Equatorial (Ra, Dec)   -- True coordinates (radians)
//   2. Horizontal (Az, Alt)   -- Telescope coordinates(radians)
//   3. Motor (Az_m, Alt_m)    -- Motor positions assumed (steps)
//   4. Encoders (Az_e, Alt_e) -- Encoder readings (counts)

//  Target acquisition:
//    - Acquire target, first 3 points(request 3 + 3 floats and 3 ints)
//    - Slew to target in alloted time
//    - Once at target, calculate required speed to next target, slew
//    - Get new coordinates for next point

//  Alignment 2 or 3 star calibration:
//    - Python picks a star, initiates Arduino calibration mode
//    - User slews to target star, when acquired, they hit a key/button
//    - Arduino sets reference star in system, az, alt, ra, dec, and t
//    - Process is repeated at least one more time, and at most 2
//
//  Tracking details:
//    - Arduino acquires new target, gets horizontal coordinates 
//    - Arduino calculates slew speed based on time it needs to be there 
//
//  PS3 Controller:
//    - If stick is in 0 position, slewing stops, need to change featuer s.t.
//      slewing speed is controlled, rather than destination, or set a max diff.

#include <AccelStepper.h>
#include <Serial.h>
#include <Wire.h>
//#include "TeleCoords.h"
//#include "Axes.h"   // Not sure how this will be employed yet.

#define DEBUG
#define LOG_DEBUG(msg) Serial.println(msg)

// AccelStepper Declarations
AccelStepper stepper1(1, 10, 11);
AccelStepper stepper2(1, 12, 13);
//                       |  |
//                       |  \-- Dir Pin
//                       \---- Step Pin

char comm[5];
boolean newComm = 0;
boolean bAltStopOverride = false;
boolean bEnableStops = false;
boolean bUseEncoders = false;
unsigned long timeout = 0;
unsigned long laseI = 0;
float az, alt, ra, dec, t;

// Approximate coordinate conversions
int az_to_mot =  3947; // steps/radian
int alt_to_mot = 1528; // steps/radian

// declarations for tracking variables
int cycl_i = 0;
float az_t[3], alt_t[3];                   // Target coordinates, radians
int az_goto = 0, alt_goto = 0, tempIn1 = 0, tempIn2 = 0; // GoTo coordinates -- will be integrated eventually into another variable
float az_spd, alt_spd;
long dt;
long time_t[3]; // Target time hack, ms from reference
//TeleCoords coords;
// Calibration variable declarations
double l[3][3]; 

#define SLAVE_ADDRESS 8


int countAlt = 0;
int countAz = 0;
int altStop = 0;
int altStopLast = 0;

// ##### SETUP ###### //
void setup() {
  /* Init I2C */
  Wire.begin(); // as master
  
  /* Init Steppers */
  stepper1.setMaxSpeed(500);
  stepper1.setAcceleration(1000);
  stepper2.setMaxSpeed(500);
  stepper2.setAcceleration(1000);
  /* ------------ */
  
  Serial.begin(115200);
  //TeleCoords coords = TeleCoords(); // Initialize coordinate transform. lib.
}

// ##### MAIN LOOP ###### //
void loop() {
  // AccelStepper Run calls need to be called as frequently as possible (moves are blocking)
    stepper1.run();
    stepper2.run();
  getCommand();
  processCommand();
  //getEncoders();
  //checkStop();
}


// ##### FUNCTIONS ###### //
void getCommand() {
  if (Serial.available() > 0) {
    int bytes_recv = 0;
    comm[4] = '\0';
    while (bytes_recv < 4) {
      if (Serial.available() > 0) {
        comm[bytes_recv++] = Serial.read();
      }
    }
    newComm = 1;
    Serial.println("recv");
  }
}

void processCommand() {
  if (newComm) {
    if (strcmp(comm,"test") == 0) {
      Serial.println("done");
    // Command to slew incrementally
    } else if (strcmp(comm,"move") == 0) {    
    
      Serial.println("done");
      tempIn1 = serialGetInt();
      tempIn2 = serialGetInt();

      // only move if allowed
      if (!bAltStopOverride) {
        az_goto  = ((tempIn1 == 0) ? stepper2.currentPosition() : az_goto  + tempIn1);
        alt_goto = ((tempIn2 == 0) ? stepper1.currentPosition() : alt_goto + tempIn2);
      
        stepper1.moveTo(alt_goto);
        stepper2.moveTo(az_goto);
      }
      
      Serial.println("done");
    
    // Reset overrides
    } else if (strcmp(comm,"rset") == 0) {
      Serial.println("done");
      bAltStopOverride = false;
      startMotors();
      Serial.println("done");
     
    // New Target
    } else if (strcmp(comm,"ntgt") == 0) {    // Command to acquire a new target
    
      Serial.println("done");
      LOG_DEBUG("Acquiring new target");
      for (int i = 0; i < 3; i++) { az_t[i]   = serialGetFloat(); }
      for (int i = 0; i < 3; i++) { alt_t[i]  = serialGetFloat(); }
      for (int i = 0; i < 3; i++) { time_t[i] = serialGetInt();   }
      cycl_i = 2; // the position in the arrays that will be overwritten first. last in last out. 
      Serial.println("done");
    
    // Update Target
    } else if (strcmp(comm,"utgt") == 0) {   // Command to update a current target's coordinates
    
      Serial.println("done");
      cycl_i = (cycl_i + 1) % 3; // LILO replacement
      az_t[cycl_i]   = serialGetFloat();
      alt_t[cycl_i]  = serialGetFloat();
      time_t[cycl_i] = serialGetInt();
      Serial.println("done");
      calculateSpeeds();
    
    // Check System
    } else if (strcmp(comm,"chck") == 0) {
      
      Serial.println("done");
       Serial.println(cycl_i);
       Serial.println(mod(cycl_i-2,3));
       Serial.println(mod(cycl_i-1,3));
       for (int i = 0; i < 3; i++) { Serial.println(az_t[i], 6); }
       for (int i = 0; i < 3; i++) { Serial.println(alt_t[i], 6); }
       for (int i = 0; i < 3; i++) { Serial.println(time_t[i]); }
      Serial.println(az_spd, 6);
      Serial.println(alt_spd,6);
      Serial.println(dt);
      Serial.println("done");
      
    // Get Position (radians?)
    } else if (strcmp(comm,"gpos") == 0) { 
      
      Serial.println("done");
      LOG_DEBUG("Ready to send position data");
      Serial.println("int");
      Serial.println(az_goto);
      Serial.println("int");
      Serial.println(alt_goto);
      Serial.println("done");
    
    // Get Position (encoder counts)
    } else if (strcmp(comm,"gcnt") == 0) {
      Serial.println("done");
      getEncoders(); // Update encoder info
      LOG_DEBUG("Ready to send count data");
      Serial.println("int");
      Serial.println(countAz);
      Serial.println("int");
      Serial.println(countAlt);
      Serial.println("int");
      Serial.println(altStop);
      Serial.println("done");
      
    // Receive position
    } else if (strcmp(comm, "satg") == 0) {
      
      Serial.println("done"); // Say we're done with the command so we can get our floats
      LOG_DEBUG("Ready to receive float"); // not necessary, just for demo
      az = serialGetFloat();
      Serial.println(az,4);
      alt = serialGetFloat();
      Serial.println(alt,4);
      Serial.println("done");
      
    } else if (strcmp(comm,"lase") == 0) {
      
      Serial.println("done"); 
      LOG_DEBUG("Ready to receive LASER input");
      laseI = serialGetInt();
      Serial.println(laseI, DEC);
      Serial.println("done");
      
    } else {
      
      Serial.println("fail");
      Serial.println("done");
      
    }
  }
  newComm = 0; // reset the command indicator switch
}

void getEncoders() {
  Wire.requestFrom(SLAVE_ADDRESS, 5); // request 4 bytes (2 integers) from slave
  countAlt  = Wire.read();
  countAlt |= Wire.read() << 8;
  countAz   = Wire.read();
  countAz  |= Wire.read() << 8;
  altStop   = Wire.read();
}

// Function that updates required motor speeds and directions
void calculateSpeeds() {
  unsigned int nxt = mod(cycl_i-1,3);
  unsigned int cur = mod(cycl_i-2,3);
  dt      = time_t[nxt] - time_t[cur];
  //az_spd  = (az_to_mot * 1000 * (az_t[nxt]   - az_t[cur]))  / dt;
  //alt_spd = (alt_to_mot *1000 * (alt_t[nxt]  - alt_t[cur])) / dt;
  az_spd  =  (az_t[nxt]   - az_t[cur]); /// dt;
  alt_spd = (alt_t[nxt]  - alt_t[cur]);/// dt;
}

// ###### Serial Communication ######
// Request and process a float over the serial line
float serialGetFloat(){
	union u_tag {
          byte bytes[4];
          float val;
        } F;
	int nbytes = 0;
	bool recv = false;

	Serial.println("float"); // Tell python we're ready to receive a float!
	timeout = millis();
        while ((!recv) & ((millis()-timeout) < 1000)){
		if (Serial.available() > 0) {
			while(nbytes < 4)
				if(Serial.available() > 0){
					F.bytes[nbytes] = Serial.read();
					nbytes++;
				}
			recv = true;
		}
	}
	Serial.println("done");
        debugFloat(F.val);
	return F.val;
}

// Request and process an integer over the serial line. 
//  This is a 4 byte request, processed as a long
int serialGetInt() {
	union u_tag {
          byte bytes[4];
          int val;
        } I;
	int nbytes = 0;

	bool recv = false;
	Serial.println("int"); // Tell python we're ready to receive an integer!
	timeout = millis();
        while ((!recv) & ((millis()-timeout) < 1000)){
		if (Serial.available() > 0) {
			while(nbytes < 4)
				if(Serial.available() > 0){
					I.bytes[nbytes] = Serial.read();
					nbytes++;
				}
			recv = true;
		}
	}
	Serial.println("done");
        debugInt(I.val);
	return I.val;
}

void checkStop() {
  if (bEnableStops) {
    if (altStopLast != altStop)  {
      if (altStopLast == 1) { // falling is okay
        altStopLast = altStop; // 0
      } else { // rising is our stop condition
        bAltStopOverride = true;
        stopMotors();
        altStopLast = altStop; // 1
      }
    }
  }
}

void startMotors() {
  stepper1.setAcceleration(1000);
  stepper2.setAcceleration(1000);
}

void stopMotors() {
  // Stop motors as quickly as possible
  //stepper1.stop();
  //stepper2.stop();
  // Zero out and pending moves
  setToCurrentPos();
  stepper1.setAcceleration(10000);
  stepper2.setAcceleration(10000);
  stepper1.moveTo(alt_goto);
  stepper2.moveTo(az_goto);
}

void setToCurrentPos() {
  alt_goto = stepper1.currentPosition();
  az_goto  = stepper2.currentPosition();
}

void debugFloat(float val) {
  #ifdef DEBUG
    Serial.println(val, 6);
  #endif
}

void debugInt(int val) {
  #ifdef DEBUG
    Serial.println(val);
  #endif
}

// #### Helper Functions ####
unsigned int mod(int a, int b) {
  int r = a % b; // remainder
  return r < 0 ? r + b : r;
}


