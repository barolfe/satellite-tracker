#include <Arduino.h>
#include "TeleCoords.h"
#define DEBUG

TeleCoords::TeleCoords() {
  _t0 = 0.0;
  _k = 1.002737908; // 24 hr solar day / sidereal day
  _isSetRef = 0;
  _isSetT   = 0;

}
bool TeleCoords::setRef(float az, float alt, float ra, float dec, float t, int n) {
  switch (n) {
    case 0:
      setH(az, alt, _l1);
      setE(ra, dec, t, _L1);
      return true;
    case 1:
      setH(az, alt, _l2);
      setE(ra, dec, t, _L2);
      return true;
    case 2:
      setH(az, alt, _l3);
      setE(ra, dec, t, _L3);
      _isSetRef = 1;
      setT();
      return true;
    default:
      return false;
  }
}

bool TeleCoords::setT() {
  float l[3][3], L[3][3], iL[3][3];
  if (_isSetRef) {
    l[0][0] = _l1[0];  l[0][1] = _l2[0];  l[0][2] = _l3[0];
    l[1][0] = _l1[1];  l[1][1] = _l2[1];  l[1][2] = _l3[1];
    l[2][0] = _l1[2];  l[2][1] = _l2[2];  l[2][2] = _l3[2];
    
    L[0][0] = _L1[0];  L[0][1] = _L2[0];  L[0][2] = _L3[0];
    L[1][0] = _L1[1];  L[1][1] = _L2[1];  L[1][2] = _L3[1];
    L[2][0] = _L1[2];  L[2][1] = _L2[2];  L[2][2] = _L3[2];
    
    inverse(L, iL);
    matrixMultiply(l, iL, _T);
    inverse(_T, _iT); 
    _isSetT = 1;
    #ifdef DEBUG
        printArray(_T,3);
    #endif
    return true;
  } else {
    return false;
  }
  
}
bool TeleCoords::getH(float ra, float dec, float t, float *az, float *alt) {
  float H[3];
  float E[3];
  if (_isSetT) {
    setE(ra, dec, t, E);
    // Matrix dot vector
    H[0] = _T[0][0]*E[0] + _T[0][1]*E[1] + _T[0][2]*E[2];
    H[1] = _T[1][0]*E[0] + _T[1][1]*E[1] + _T[1][2]*E[2];
    H[2] = _T[2][0]*E[0] + _T[2][1]*E[1] + _T[2][2]*E[2];
    
    (*az)  = atan2(H[1], H[0]);
    (*alt) = asin(H[2]); 
    
    return true;
  } else {
    return false;
  } 
}

bool TeleCoords::getE(float az, float alt, float t, float *ra, float *dec) {
  float H[3];
  float E[3];
  if (_isSetT) {
    setH(az, alt, H);
    // Matrix dot vector
    E[0] = _iT[0][0]*H[0] + _iT[0][1]*H[1] + _iT[0][2]*H[2];
    E[1] = _iT[1][0]*H[0] + _iT[1][1]*H[1] + _iT[1][2]*H[2];
    E[2] = _iT[2][0]*H[0] + _iT[2][1]*H[1] + _iT[2][2]*H[2];
    
    (*ra)  = atan2(E[1], E[0]) + _k * (t-_t0);
    (*dec) = asin(E[2]); 
    
    return true;
  } else {
    return false;
  }
  
}
void TeleCoords::setH(float az, float alt, float *H) {
  H[0] = cos(alt) * cos(az);
  H[1] = cos(alt) * sin(az);
  H[2] = sin(alt);
}

void TeleCoords::setE(float ra, float dec, float t, float *E) {
  E[0] = cos(dec) * cos(ra - _k*2*M_PI * (t-_t0));
  E[1] = cos(dec) * sin(ra - _k*2*M_PI * (t-_t0));
  E[2] = sin(dec);  
}

void TeleCoords::setRefT(float t) {
  _t0 = t;
}


// Matrix Math functions
float TeleCoords::inverse(float a[3][3], float b[3][3]) {
  int i, j, i2, j2, i3, j3;
  float d;
  float c[2][2];
  for (i = 0; i < 3; i++) {
    for (j = 0; j < 3; j++) {
      i3 = 0; 
      for (i2 = 0; i2 < 3; i2++) {
        if (i2 != i) {
          j3 = 0;
          for (j2 = 0; j2 < 3; j2++) {
            if (j2 != j) {
              c[i3][j3] = a[i2][j2];
              j3++;
            }
          }
          i3++;
        }
    }
    b[i][j] = pow(-1.0,i+j+2.0) * det2by2(c);
  }
 }
 transpose(b);
 d = det3by3(a);
 for (i = 0; i < 3; i++) {
   for (j = 0; j < 3; j++) {
     b[i][j] *= (1.0/d);
   }
 }
}

float TeleCoords::det2by2(float a[2][2]) {
  return (a[0][0]*a[1][1] - a[0][1]*a[1][0]);
}

float TeleCoords::det3by3(float a[3][3]) {
  float det = 0;
  det =  a[0][0]*(a[1][1]*a[2][2] - a[1][2]*a[2][1]);
  det -= a[0][1]*(a[1][0]*a[2][2] - a[1][2]*a[2][0]);
  det += a[0][2]*(a[1][0]*a[2][1] - a[1][1]*a[2][0]);
  return det;
}

void TeleCoords::matrixMultiply(float a[3][3], float b[3][3], float c[3][3]) {
  int i, j, i2;
  for (i = 0; i < 3; i++) {
   for (j = 0; j < 3; j++) {
     c[i][j] = 0;
     for (i2 = 0; i2 < 3; i2++) {
       c[i][j] += a[i][i2]*b[i2][j];
     }
   }
  }
}
void TeleCoords::transpose(float a[3][3]) {
  int i, j;
  float tmp;
  for (i = 0; i < 3; i++) {
    for (j = i; j < 3; j++) {
      tmp = a[i][j];
      a[i][j] = a[j][i];
      a[j][i] = tmp;
    }
  }
}

void TeleCoords::printArray(float a[3][3], int n) {
  int i, j;
  for (i = 0; i < n; i++) {
    for (j = 0; j < n; j++) {
      Serial.print("[");
      Serial.print(a[i][j],4);
      Serial.print("]");
    }
    Serial.println();
  }
  Serial.println();
}

