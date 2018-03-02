// $Id: fftgrid3d.cpp 1702 2017-10-16 12:17:34Z fjellvoll $

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

#include "fftgrid3d.hpp"

#include <mkl_dfti.h>

namespace NRLib {

template <>
void NRLibPrivate::ComputeFFT3D<double>(size_t ni, size_t nj, size_t nk,
                                        double* in, std::complex<double>* out)
{
  DFTI_DESCRIPTOR_HANDLE descriptor;
  MKL_LONG status, size[3];

  size[0] = static_cast<MKL_LONG>(ni);
  size[1] = static_cast<MKL_LONG>(nj);
  size[2] = static_cast<MKL_LONG>(nk);


  status = DftiCreateDescriptor(&descriptor, DFTI_DOUBLE, DFTI_REAL, 3, size); //Specify size and precision
  status = DftiSetValue(descriptor, DFTI_PLACEMENT, DFTI_NOT_INPLACE); //Out of place FFT
  status = DftiCommitDescriptor(descriptor); //Finalize the descriptor
  status = DftiComputeForward(descriptor, in, out); //Compute the Forward FFT
  status = DftiFreeDescriptor(&descriptor); //Free the descriptor
  assert(status == 0);
}


template <>
void NRLibPrivate::ComputeFFT3DInverse<double>(size_t ni, size_t nj, size_t nk,
                                               std::complex<double>* in, double* out)
{
  DFTI_DESCRIPTOR_HANDLE descriptor;
  MKL_LONG status, size[3];

  size[0] = static_cast<MKL_LONG>(ni);
  size[1] = static_cast<MKL_LONG>(nj);
  size[2] = static_cast<MKL_LONG>(nk);

  status = DftiCreateDescriptor(&descriptor, DFTI_DOUBLE, DFTI_REAL, 3, size); //Specify size and precision
  status = DftiSetValue(descriptor, DFTI_PLACEMENT, DFTI_NOT_INPLACE); //Out of place FFT
  //status = DftiSetValue(descriptor, DFTI_BACKWARD_SCALE, 1.0 / (ni*nj*nk)); //Scale down the output
  status = DftiCommitDescriptor(descriptor); //Finalize the descriptor
  status = DftiComputeBackward(descriptor, in, out); //Compute the Backward FFT
  status = DftiFreeDescriptor(&descriptor); //Free the descriptor
  assert(status == 0);
}


template <>
void NRLibPrivate::ComputeFFT3D<float>(size_t ni, size_t nj, size_t nk,
                                       float* in, std::complex<float>* out)
{
  DFTI_DESCRIPTOR_HANDLE descriptor;
  MKL_LONG status, size[3];

  size[0] = static_cast<MKL_LONG>(ni);
  size[1] = static_cast<MKL_LONG>(nj);
  size[2] = static_cast<MKL_LONG>(nk);


  status = DftiCreateDescriptor(&descriptor, DFTI_SINGLE, DFTI_REAL, 3, size); //Specify size and precision
  status = DftiSetValue(descriptor, DFTI_PLACEMENT, DFTI_NOT_INPLACE); //Out of place FFT
  status = DftiCommitDescriptor(descriptor); //Finalize the descriptor
  status = DftiComputeForward(descriptor, in, out); //Compute the Forward FFT
  status = DftiFreeDescriptor(&descriptor); //Free the descriptor
  assert(status == 0);
}


template <>
void NRLibPrivate::ComputeFFT3DInverse<float>(size_t ni, size_t nj, size_t nk,
                                              std::complex<float>* in, float* out)
{
  DFTI_DESCRIPTOR_HANDLE descriptor;
  MKL_LONG status, size[3];

  size[0] = static_cast<MKL_LONG>(ni);
  size[1] = static_cast<MKL_LONG>(nj);
  size[2] = static_cast<MKL_LONG>(nk);

  status = DftiCreateDescriptor(&descriptor, DFTI_SINGLE, DFTI_REAL, 3, size); //Specify size and precision
  status = DftiSetValue(descriptor, DFTI_PLACEMENT, DFTI_NOT_INPLACE); //Out of place FFT
  //status = DftiSetValue(descriptor, DFTI_BACKWARD_SCALE, 1.0f / (ni*nj*nk)); //Scale down the output
  status = DftiCommitDescriptor(descriptor); //Finalize the descriptor
  status = DftiComputeBackward(descriptor, in, out); //Compute the Backward FFT
  status = DftiFreeDescriptor(&descriptor); //Free the descriptor
  assert(status == 0);
}

} // namespace NRLib
