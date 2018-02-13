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

#include "fftcovgrid.hpp"
#include "variogram.hpp"

#include <algorithm>

using namespace NRLib;

// Local utility functions that are inexpensive and can be used
// independent of the number of dimensions
namespace NRLib { namespace FFTCovGridUtilities
{
  std::vector<double> FindVariogramRanges(const Variogram & variogram)
  {
    // Project the three directions of the variogram onto
    // the axis and find the longest range in each axis
    // direction. This function could potentially have
    // been part of the Variogram class.

    double xmax = 0.0;
    double ymax = 0.0;
    double zmax = 0.0;
    double azi = variogram.GetAzimuthAngle();
    double dip = variogram.GetDipAngle();
    // Project the main direction onto the axes
    double main_vector[3] = {fabs(variogram.GetRangeX() * cos(dip) * cos(azi)),
                             fabs(variogram.GetRangeX() * cos(dip) * sin(azi)),
                             fabs(variogram.GetRangeX() * sin(dip))};

    // Project perpendicular vector onto the axes
    double perp_vector[3] = {fabs(variogram.GetRangeY() * cos(azi + 3.14 / 2.0)),  // TODO: replace with PI
                             fabs(variogram.GetRangeY() * sin(azi + 3.14 / 2.0)),
                             0.0};

    // Project final vector onto the axes
    double down_vector[3] = {fabs(variogram.GetRangeZ() * cos(dip + 3.14 / 2.0) * cos(azi)), // TODO: replace with PI
                             fabs(variogram.GetRangeZ() * cos(dip + 3.14 / 2.0) * sin(azi)),
                             fabs(variogram.GetRangeZ() * sin(dip + 3.14 / 2.0))};

    xmax = std::max(main_vector[0], perp_vector[0]);
    ymax = std::max(main_vector[1], perp_vector[1]);
    zmax = std::max(main_vector[2], perp_vector[2]);

    xmax = std::max(xmax, down_vector[0]);
    ymax = std::max(ymax, down_vector[1]);
    zmax = std::max(zmax, down_vector[2]);

    std::vector<double> axis_ranges;
    axis_ranges.push_back(xmax);
    axis_ranges.push_back(ymax);
    axis_ranges.push_back(zmax);

    return axis_ranges;
  }

  std::vector<double> FindSmoothingFactors(const Variogram & variogram,
                                          double            scaling_x,
                                          double            scaling_y,
                                          double            scaling_z)
  {
    // Using too small scaling factors is unstable
    assert(scaling_x > 1e-12);
    assert(scaling_y > 1e-12);
    assert(scaling_z > 1e-12);
    std::vector<double> axis_ranges = FFTCovGridUtilities::FindVariogramRanges(variogram);

    double sx = pow(scaling_x, 1.0/(axis_ranges[0] * axis_ranges[0]));
    double sy = pow(scaling_y, 1.0/(axis_ranges[1] * axis_ranges[1]));
    double sz = pow(scaling_z, 1.0/(axis_ranges[2] * axis_ranges[2]));

    std::vector<double> scaling_factors;
    scaling_factors.push_back(sx);
    scaling_factors.push_back(sy);
    scaling_factors.push_back(sz);

    return scaling_factors;
  }
}
}

/*******************************************************/
/* FFT Covariance grid, 1D                             */
/*******************************************************/

FFTCovGrid1D::FFTCovGrid1D(const Variogram & variogram,
                           int               nx,
                           double            dx,
                           double            scaling_x)
: cov_(nx)
{
  InitializeSmoothingFactors(variogram, scaling_x);
  bool apply_scaling_x = scaling_x < 0.99999;

  int nxm = (nx + 1) / 2;
  for (int i = 0; i < nxm; i++) {
    cov_[i] = variogram.GetCov(i*dx);
    if (apply_scaling_x) cov_[i] *= FindSmoothingFactorX(i*dx);
  }
  for (int i = nxm; i < nx; i++) {
    double ddx = dx*(nx - i);
    cov_[i] = variogram.GetCov(ddx);
    if (apply_scaling_x) cov_[i] *= FindSmoothingFactorX(ddx);
  }
}

void FFTCovGrid1D::InitializeSmoothingFactors(const Variogram & variogram,
                                              double            scaling_x)
{
  std::vector<double> scaling_factors = FFTCovGridUtilities::FindSmoothingFactors(variogram,
                                                                                  scaling_x,
                                                                                  1.0,
                                                                                  1.0);

  sx_ = scaling_factors[0];
}

/*******************************************************/
/* FFT Covariance grid, 2D                             */
/*******************************************************/

FFTCovGrid2D::FFTCovGrid2D(const Variogram & variogram,
                           int               nx,
                           double            dx,
                           int               ny,
                           double            dy,
                           double            scaling_x,
                           double            scaling_y)
:
cov_(nx, ny)
{
  InitializeSmoothingFactors(variogram, scaling_x, scaling_y);
  bool apply_scaling_x = scaling_x < 0.99999;
  bool apply_scaling_y = scaling_y < 0.99999;

  int nxm = (nx + 1) / 2;
  int nym = (ny + 1) / 2;
  double ddx, ddy;
  int i, j;
  for (j = 0; j < nym; j++) {
    ddy = j * dy;
    for (i = 0; i < nxm; i++) {
      ddx = i * dx;
      cov_(i, j) = variogram.GetCov(ddx, ddy);
      if (apply_scaling_x) cov_(i, j) *= FindSmoothingFactorX(ddx);
      if (apply_scaling_y) cov_(i, j) *= FindSmoothingFactorY(ddy);
    }
    // -1 - i quadrant
    for (i = nxm; i < nx; i++) {
      ddx = (i - nx) * dx;
      cov_(i, j) = variogram.GetCov(ddx, ddy);
      if (apply_scaling_x) cov_(i, j) *= FindSmoothingFactorX(ddx);
      if (apply_scaling_y) cov_(i, j) *= FindSmoothingFactorY(ddy);
    }
  }

  // 1 + i quadrant
  for (j = nym; j < ny; j++) {
    ddy = (j - ny) * dy;
    for (i = nxm; i < nx; i++) {
      ddx = (i - nx)* dx;
      cov_(i, j) = variogram.GetCov(ddx, ddy);
      if (apply_scaling_x) cov_(i, j) *= FindSmoothingFactorX(ddx);
      if (apply_scaling_y) cov_(i, j) *= FindSmoothingFactorY(ddy);
    }
    // -1 + i quadrant
    for (i = 0; i < nxm; i++) {
      ddx = i*dx;
      cov_(i, j) = variogram.GetCov(ddx, ddy);
      if (apply_scaling_x) cov_(i, j) *= FindSmoothingFactorX(ddx);
      if (apply_scaling_y) cov_(i, j) *= FindSmoothingFactorY(ddy);
    }
  }
}

void FFTCovGrid2D::InitializeSmoothingFactors(const Variogram & variogram,
                                              double            scaling_x,
                                              double            scaling_y)
{
  std::vector<double> scaling_factors = FFTCovGridUtilities::FindSmoothingFactors(variogram,
                                                                                  scaling_x,
                                                                                  scaling_y,
                                                                                  1.0);

  sx_ = scaling_factors[0];
  sy_ = scaling_factors[1];
}

/*******************************************************/
/* FFT Covariance grid, 3D                             */
/*******************************************************/


FFTCovGrid3D::FFTCovGrid3D(const Variogram & variogram,
                           int               nx,
                           double            dx,
                           int               ny,
                           double            dy,
                           int               nz,
                           double            dz,
                           double            scaling_x,
                           double            scaling_y,
                           double            scaling_z)
:
cov_(nx, ny, nz)
{
  InitializeSmoothingFactors(variogram, scaling_x, scaling_y, scaling_z);
  bool apply_scaling_x = scaling_x < 0.99999;
  bool apply_scaling_y = scaling_y < 0.99999;
  bool apply_scaling_z = scaling_z < 0.99999;

  int nxm = (nx + 1) / 2;
  int nym = (ny + 1) / 2;
  int nzm = (nz + 1) / 2;
  double ddx, ddy, ddz;
  int i, j, k;
  for (k = 0; k < nzm; k++) {
    ddz = k * dz;
    for (j = 0; j < nym; j++) {
      ddy = j * dy;
      for (i = 0; i < nxm; i++) {
        ddx = i * dx;
        cov_(i, j, k) = variogram.GetCov(ddx, ddy, ddz);
        if (apply_scaling_x) cov_(i, j, k) *= FindSmoothingFactorX(ddx);
        if (apply_scaling_y) cov_(i, j, k) *= FindSmoothingFactorY(ddy);
        if (apply_scaling_z) cov_(i, j, k) *= FindSmoothingFactorZ(ddz);
      }

      for (i = nxm; i < nx; i++) {
        ddx = (i - nx) * dx;
        cov_(i, j, k) = variogram.GetCov(ddx, ddy, ddz);
        if (apply_scaling_x) cov_(i, j, k) *= FindSmoothingFactorX(ddx);
        if (apply_scaling_y) cov_(i, j, k) *= FindSmoothingFactorY(ddy);
        if (apply_scaling_z) cov_(i, j, k) *= FindSmoothingFactorZ(ddz);
      }
    }
  }

  for (k = 0; k < nzm; k++) {
    ddz = k * dz;
    for (j = nym; j < ny; j++) {
      ddy = (j - ny) * dy;
      for (i = nxm; i < nx; i++) {
        ddx = (i - nx)* dx;
        cov_(i, j, k) = variogram.GetCov(ddx, ddy, ddz);
        if (apply_scaling_x) cov_(i, j, k) *= FindSmoothingFactorX(ddx);
        if (apply_scaling_y) cov_(i, j, k) *= FindSmoothingFactorY(ddy);
        if (apply_scaling_z) cov_(i, j, k) *= FindSmoothingFactorZ(ddz);
      }

      for (i = 0; i < nxm; i++) {
        ddx = i*dx;
        cov_(i, j, k) = variogram.GetCov(ddx, ddy, ddz);
        if (apply_scaling_x) cov_(i, j, k) *= FindSmoothingFactorX(ddx);
        if (apply_scaling_y) cov_(i, j, k) *= FindSmoothingFactorY(ddy);
        if (apply_scaling_z) cov_(i, j, k) *= FindSmoothingFactorZ(ddz);
      }
    }
  }

  for (k = nzm; k < nz; k++) {
    ddz = (k - nz) * dz;
    for (j = 0; j < nym; j++) {
      ddy = j * dy;
      for (i = 0; i < nxm; i++) {
        ddx = i * dx;
        cov_(i, j, k) = variogram.GetCov(ddx, ddy, ddz);
        if (apply_scaling_x) cov_(i, j, k) *= FindSmoothingFactorX(ddx);
        if (apply_scaling_y) cov_(i, j, k) *= FindSmoothingFactorY(ddy);
        if (apply_scaling_z) cov_(i, j, k) *= FindSmoothingFactorZ(ddz);
      }

      for (i = nxm; i < nx; i++) {
        ddx = (i - nx) * dx;
        cov_(i, j, k) = variogram.GetCov(ddx, ddy, ddz);
        if (apply_scaling_x) cov_(i, j, k) *= FindSmoothingFactorX(ddx);
        if (apply_scaling_y) cov_(i, j, k) *= FindSmoothingFactorY(ddy);
        if (apply_scaling_z) cov_(i, j, k) *= FindSmoothingFactorZ(ddz);
      }
    }
  }


  for (k = nzm; k < nz; k++) {
    ddz = (k - nz) * dz;
    for (j = nym; j < ny; j++) {
      ddy = (j - ny) * dy;
      for (i = 0; i < nxm; i++) {
        ddx = i * dx;
        cov_(i, j, k) = variogram.GetCov(ddx, ddy, ddz);
        if (apply_scaling_x) cov_(i, j, k) *= FindSmoothingFactorX(ddx);
        if (apply_scaling_y) cov_(i, j, k) *= FindSmoothingFactorY(ddy);
        if (apply_scaling_z) cov_(i, j, k) *= FindSmoothingFactorZ(ddz);
      }

      for (i = nxm; i < nx; i++) {
        ddx = (i - nx) * dx;
        cov_(i, j, k) = variogram.GetCov(ddx, ddy, ddz);
        if (apply_scaling_x) cov_(i, j, k) *= FindSmoothingFactorX(ddx);
        if (apply_scaling_y) cov_(i, j, k) *= FindSmoothingFactorY(ddy);
        if (apply_scaling_z) cov_(i, j, k) *= FindSmoothingFactorZ(ddz);
      }
    }
  }
}


void FFTCovGrid3D::InitializeSmoothingFactors(const Variogram & variogram,
                                              double            scaling_x,
                                              double            scaling_y,
                                              double            scaling_z)
{
  std::vector<double> scaling_factors = FFTCovGridUtilities::FindSmoothingFactors(variogram,
                                                                                  scaling_x,
                                                                                  scaling_y,
                                                                                  scaling_z);

  sx_ = scaling_factors[0];
  sy_ = scaling_factors[1];
  sz_ = scaling_factors[2];
}
