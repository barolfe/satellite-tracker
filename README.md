# Satellite Tracker
A python based satellite tracker system designed to work with hardware (e.g. an Alt-Az type mount), providing easy alignment, target acquisition and following, and integration with Stellarium.

## Quick Overview
The purpose of this project developed from a desire to inform the public of fly-overs of the International Space Station. Most people live somewhere where the ISS will occasionally make a pass that is visible, and sometimes, it is the brightest object in the sky as it does so. I thought it was fascinating that there were people shooting by on that little star in the sky, but was maybe a little disappointed that no one else seemed to be looking up. 

I decided to create a device that could be easily deployed and would shine a bright enough laser at the space station as it passed over head, guiding people's eyes to it, and at least getting them to ask the question "I wonder what that is?".

## The project goals include
1. A mechanical platform with two electrically-driven rotational axes orthogonal to one another -- basically an Alt-Azimuth configuration. 
2. Code and associated hardware to automatically acquire and track targets through the sky.
3. Accurate but simple star-alignment procedure that precludes the need for an accurate and precise mechanical alignment

## Stretch goals include
1. Automatic orientation alignment by plate solving from a built-in camera (e.g. the device sees the sky above it and determines its orientation in space). 

# The code
The code is very much a work in progress, but can be described at a basic level. 

The implementation will likely be on a Raspberry Pi or similar unix-based system, with primary control occuring in a simple Python application. Low-level tasks and all mechanical direction will occur on an Arduino communicating with the control code. 

## Raspberry Pi (Python)
The python based application's role is to handle all control and processing for the tracker. This inludes:
1. Handling user input (through PS3 controller, console, etc)
2. Interfacing with Stellarium (optional)
3. Performing celestial calculations (position of the Sun, Earth, and satellites)
4. Interfacing with external databases (positions of stars, and two-line element data for satellites)
5. Communication with Arduino

I'm utilizing the powerful PyEphem library to make accurate celestial calculations, as well as provide the heavy lifting for determing satellite positions based on their Two-Line Element data. 

I'm also using PyGame to interface with a PS3 controller, which allows for easy manipulation of the tracker via the two joysticks. The buttons are also used during the aligment procedure and for other roles. 

## Arduino (C)
The Arduino's primary role is to do what the Python application tells it to. In this way, it's basically slaved to the Raspberry Pi. 

When a satellite is acquired, the Python code will instruct the Arduino to begin tracking by feeding it a list of simple GoTo instructions. Exact implementation is still being prototyped. Other instructions will include LaseOn/LaseOff, and Stop. 

Though the Arduino is slaved to the Raspberry Pi, it will have decision-making autonomy concerning the mechanics of the tracker. For example It may not be safe to lase in certain directions, and if the Arduino finds itself pointing in one of these regions, it should automatically stop lasing. There are also mechanical restrictions on the setup for an Alt-Az mount that require a bit of thinking on the Arduino's part to properly implement it's given GoTo command. 

# Project Status
The hardware for this project has been prototyped in several iterations. It's functional, but untested in a real environment. The axes use optical encoders taken from salvaged printer parts to precisely traack their positions. I decided this was necessary as the stepper motors and mechanical aspects of the system were probably not precise enough for aiming at the accuracy I desired. The other details of the setup are trivial. 

The code has seen several major overhauls. The Python portion of the project is maturing, but it is purely in a testing state at the moment, and many of the "automatic" features have yet to be implemented. On the Arduino side of things, there are still some implementation-related issues to sort out that will require further testing. 

