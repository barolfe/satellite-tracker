#include "Arduino.h"
#include "Axes.h"


Axes::Axes(int I, int Q, int interruptN)
{
	_pos = 0;
	_encoderI = I;
	_encoderQ = Q;

	pinMode(_encoderI, INPUT);
  	pinMode(_encoderQ, INPUT);
}

int Axes::getPos()
{
	return _pos;
}

void Axes::setPos(int pos)
{
	_pos = pos;
}
