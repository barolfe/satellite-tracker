#ifndef TeleCoords_h
#define TeleCoords_h


#include <cmath.h>

class TeleCoords {

	private:
                float _l1[3], _l2[3], _l3[3], _L1[3], _L2[3], _L3[3];
		float _T[3][3], _iT[3][3];
		float _t0;
		float _k; // 24 hr solar day / sidereal day
		bool _isSetRef;
		bool _isSetT;

	public:
		TeleCoords(); // Constructor 
		bool setRef(float az, float alt, float ra, float dec, float t, int n);
		bool setT();
		bool getH(float ra, float dec, float t, float *az, float *alt);
		bool getE(float az, float alt, float t, float *ra, float *dec);
		void setH(float az, float alt, float *H);
		void setE(float ra, float dec, float t, float *E);
		void setRefT(float t);
		float inverse(float a[3][3], float b[3][3]);
		float det2by2(float a[2][2]);
		float det3by3(float a[3][3]);
		void matrixMultiply(float a[3][3], float b[3][3], float c[3][3]);
		void transpose(float a[3][3]);
		void printArray(float a[3][3], int n);
};

#endif
