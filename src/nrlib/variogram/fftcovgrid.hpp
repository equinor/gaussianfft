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

#ifndef NRLIB_VARIOGRAM_FFTCOVGRID_HPP
#define NRLIB_VARIOGRAM_FFTCOVGRID_HPP

#include <cmath>

#include "../grid/grid.hpp"
#include "../grid/grid2d.hpp"

namespace NRLib {
class Variogram;

/// Class for generating the 1D FFT grid for simulation of Gaussian Fields
/// Can also apply correlation function smoothing if the scaling parameters
/// are set to something between 0.0 and 1.0. Scaling is how much the
/// correlation function is scaled at 1 range (after projecting the directions
/// of the variogram)
class FFTCovGrid1D {
public:
  FFTCovGrid1D(const Variogram & vario,
               int               nx,
               double            dx,
               double            scaling_x = 1.0);

  const std::vector<double> GetCov() const { return cov_; }
private:
  std::vector<double> cov_;

  double sx_;

  void InitializeSmoothingFactors(const Variogram & variogram,
                                  double            scaling_x);

  double FindSmoothingFactorX(double ddx) { return pow(sx_, ddx * ddx); }
};

/// Same as FFTCovGrid1D, but for two dimensions
class FFTCovGrid2D {
public:
  FFTCovGrid2D(const Variogram & vario,
               int               nx,
               double            dx,
               int               ny,
               double            dy,
               double            scaling_x = 1.0,
               double            scaling_y = 1.0);

  const NRLib::Grid2D<double> GetCov() const { return cov_; }
private:
  NRLib::Grid2D<double> cov_;

  double sx_;
  double sy_;

  void InitializeSmoothingFactors(const Variogram & variogram,
                                  double            scaling_x,
                                  double            scaling_y);

  double FindSmoothingFactorX(double ddx) { return pow(sx_, ddx * ddx); }

  double FindSmoothingFactorY(double ddy) { return pow(sy_, ddy * ddy); }
};

/// Same as FFTCovGrid1D, but for three dimensions
class FFTCovGrid3D {
public:
  FFTCovGrid3D(const Variogram & vario,
               int               nx,
               double            dx,
               int               ny,
               double            dy,
               int               nz,
               double            dz,
               double            scaling_x = 1.0,
               double            scaling_y = 1.0,
               double            scaling_z = 1.0);

  const NRLib::Grid<double> GetCov() const { return cov_; }
private:
  Grid<double> cov_;

  double sx_;
  double sy_;
  double sz_;

  void InitializeSmoothingFactors(const Variogram & variogram,
                                  double            scaling_x,
                                  double            scaling_y,
                                  double            scaling_z);

  double FindSmoothingFactorX(double ddx) { return pow(sx_, ddx * ddx); }

  double FindSmoothingFactorY(double ddy) { return pow(sy_, ddy * ddy); }

  double FindSmoothingFactorZ(double ddz) { return pow(sz_, ddz * ddz); }
};

}

#endif // NRLIB_VARIOGRAM_FFTCOVGRID_HPP
