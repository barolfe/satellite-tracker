/* Axes.h - A small library with which to create feedback
objects for slew axies in Alt/Az setup
*/

#ifndef Axes_h
#define Axes_h

#include "Arduino.h"

class Axes
{
  public:
    Axes(int I, int Q, int interruptN);
    int getPos();
    void setPos(int pos);
  private:
    int _pos;
    int _encoderI;
    int _encoderQ;
    void handleEncoder();
    volatile int _count;
};

#endif
