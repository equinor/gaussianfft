// $Id: fft.cpp 1702 2017-10-16 12:17:34Z fjellvoll $

// Copyright (c)  2011, Norwegian Computing Center
// All rights reserved.
// Redistribution and use in source and binary forms, with or without modification,
// are permitted provided that the following conditions are met:
// •  Redistributions of source code must retain the above copyright notice, this
//    list of conditions and the following disclaimer.
// •  Redistributions in binary form must reproduce the above copyright notice, this list of
//    conditions and the following disclaimer in the documentation and/or other materials
//    provided with the distribution.
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
// EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
// OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
// SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
// OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
// HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
// OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
// EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#include "fft.hpp"
#include <mkl_dfti.h>
#include <iostream>

template <>
void NRLib::NRLibPrivate::ComputeFFT1D<double>(size_t n,
                                               double* in,
                                               std::complex<double>* out)
{

  /*  float _Complex x[32];
for (size_t i = 0; i < 32; i++) {
   float ii = static_cast<float>(i);
   x[i] = (1.0 + 1.0i) * ii;//ii/3.0i;//in[i];
   //x[i].imaginary = ii/3.0i;//in[i];
 }
DFTI_DESCRIPTOR_HANDLE my_desc1_handle;
MKL_LONG status;
 std::cout << "1!\n";
status = DftiCreateDescriptor( &my_desc1_handle, DFTI_SINGLE,
          DFTI_COMPLEX, 1, 16);
 std::cout << "2!\n";
status = DftiCommitDescriptor( my_desc1_handle );
 std::cout << "3!\n";
status = DftiComputeForward( my_desc1_handle, x);
 std::cout << "4!\n";
 status = DftiFreeDescriptor(&my_desc1_handle);*/

  float * y_in = (float *) mkl_malloc(999 * sizeof(float), 64);
//float y_out[34];
DFTI_DESCRIPTOR_HANDLE my_desc2_handle;
MKL_LONG status;
for (size_t i = 0; i < 999; i++) {
   float ii = static_cast<float>(i);
   y_in[i] = ii/3.0;//in[i];
 }
 MKL_LONG psize = 128;
status = DftiCreateDescriptor( &my_desc2_handle, DFTI_DOUBLE,
          DFTI_REAL, 1, psize);
// status = DftiSetValue( my_desc2_handle, DFTI_PLACEMENT, DFTI_NOT_INPLACE);
// status = DftiSetValue( my_desc2_handle, DFTI_WORKSPACE, DFTI_AVOID);
status = DftiCommitDescriptor( my_desc2_handle);
status = DftiComputeForward( my_desc2_handle, y_in);
status = DftiFreeDescriptor(&my_desc2_handle);

  /*
  //double * y_in = new double[128];
  //std::complex<double> * y_out = new std::complex<double>[128];
  float y_in[128];
  float y_out[130];


DFTI_DESCRIPTOR_HANDLE my_desc2_handle;
MKL_LONG status;
//...put input data into x_in[0],...,x_in[31]; y_in[0],...,y_in[31]
 for (size_t i = 0; i < 128; i++) {
   double ii = static_cast<double>(i);
   y_in[i] = ii;//in[i];
 }
 std::cout << "Create2!";
status = DftiCreateDescriptor( &my_desc2_handle, DFTI_DOUBLE,
          DFTI_REAL, 1, 128);

status = DftiSetValue( my_desc2_handle, DFTI_PLACEMENT, DFTI_NOT_INPLACE);
 std::cout << "Commit2!";
status = DftiCommitDescriptor( my_desc2_handle);
 std::cout << "Forward2!";
status = DftiComputeForward( my_desc2_handle, y_in, y_out);
 std::cout << "Free2!";
status = DftiFreeDescriptor(&my_desc2_handle);
 std::cout << "Done!";

 for (size_t i = 0; i < 34; i++) {
   std::cout << y_out[i] << std::endl;
   }*/


  //DFTI_DESCRIPTOR_HANDLE descriptor;
  //MKL_LONG status;

  /*std::cout << "Creating descriptor\n";
  status = DftiCreateDescriptor(&descriptor, DFTI_DOUBLE, DFTI_REAL, 1, n); //Specify size and precision
  std::cout << "Setting value\n";
  status = DftiSetValue(descriptor, DFTI_PLACEMENT, DFTI_NOT_INPLACE); //Out of place FFT
  std::cout << "Committing descriptor\n";
  status = DftiCommitDescriptor(descriptor); //Finalize the descriptor
  std::cout << "Computing forward\n";
  status = DftiComputeForward(descriptor, in, out); //Compute the Forward FFT
  std::cout << status;
  std::cout << "Freeing descriptor\n";
  // status = DftiFreeDescriptor(&descriptor); //Free the descriptor
  std::cout << "Done, making assertion\n";
  assert(status == 0);*/
}

template <>
void NRLib::NRLibPrivate::ComputeFFTInv1D<double>(size_t n,
                                                  std::complex<double>* in,
                                                  double* out)
{
  DFTI_DESCRIPTOR_HANDLE descriptor;
  MKL_LONG status;

  std::cout << "Creating inv descriptor\n";
  status = DftiCreateDescriptor(&descriptor, DFTI_DOUBLE, DFTI_REAL, 1, n); //Specify size and precision
  std::cout << "Setting inv value\n";
  status = DftiSetValue(descriptor, DFTI_PLACEMENT, DFTI_NOT_INPLACE); //Out of place FFT
  //status = DftiSetValue(descriptor, DFTI_BACKWARD_SCALE, 1.0 / n); //Scale down the output
  std::cout << "Committing inv desciptor\n";
  status = DftiCommitDescriptor(descriptor); //Finalize the descriptor
  std::cout << "Computing backward\n";
  status = DftiComputeBackward(descriptor, in, out); //Compute the Backward FFT
  std::cout << "Freeing inv descriptor\n";
  // status = DftiFreeDescriptor(&descriptor); //Free the descriptor
  std::cout << "Done, making inv assertion\n";
  assert(status == 0);

}

size_t
NRLib::FindNewSizeWithPadding(size_t minSize, bool must_be_even) {
  int i,j,k,l,m,n;
  size_t factor   =       1;

  int minant2 = 0;
  if (must_be_even)
    minant2 = 1;

  int maxant2    = static_cast<int>(ceil((double) log((float)(minSize)) / log(2.0f) ));
  int maxant3    = static_cast<int>(ceil((double) log((float)(minSize)) / log(3.0f) ));
  int maxant5    = static_cast<int>(ceil((double) log((float)(minSize)) / log(5.0f) ));
  int maxant7    = static_cast<int>(ceil((double) log((float)(minSize)) / log(7.0f) ));
  int maxant11   = 0;
  int maxant13   = 0;
  size_t closestprod= static_cast<size_t>(pow(2.0f,maxant2));

  // kan forbedres ved aa trekke fra i endepunktene.i for lokkene
  for (i = minant2; i < maxant2+1; i++)
    for (j = 0; j < maxant3+1; j++)
      for (k = 0; k < maxant5+1; k++)
        for (l = 0; l < maxant7+1; l++)
          for (m = 0; m < maxant11+1; m++)
            for (n = maxant11; n < maxant13+1; n++) {
              factor = static_cast<size_t> (pow(2.0f,i)*pow(3.0f,j)*pow(5.0f,k)*
                pow(7.0f,l)*pow(11.0f,m)*pow(13.0f,n));
              if ((factor >=  minSize) &&  (factor <  closestprod)) {
                closestprod = factor;
              }
            }

  return closestprod;
}
