// $Id: gaussianfield.cpp 1761 2018-03-13 07:55:09Z vegard $

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

#include <cmath>
#include <algorithm>
#include "gaussianfield.hpp"

#include "variogram.hpp"
#include "../grid/grid2d.hpp"
#include "../grid/grid.hpp"
#include "../random/random.hpp"

#include "../fft/fftgrid2d.hpp"
#include "../fft/fftgrid3d.hpp"
#include "../fft/fft.hpp"

#include "fftcovgrid.hpp"

using namespace NRLib;

/****************************************************************************************/
/* Local utility functions                                                              */
/****************************************************************************************/

size_t NRLib::FindGaussianFieldPadding(const Variogram & variogram, size_t grid_size, double range, double step)
{
  return static_cast<size_t>(
    std::max(
      static_cast<int>(variogram.GetMinimumRangeToGridRatio() * range / step - grid_size),
      static_cast<int>(range/step)
    ) + 1 // Add 1 to avoid rounding down errors
  );
}

std::vector<size_t> NRLib::FindNDimPadding(const Variogram & variogram,
                                           size_t            nx,
                                           double            dx,
                                           size_t            ny,
                                           double            dy,
                                           size_t            nz,
                                           double            dz)
{
  std::vector<size_t> pad;
  if (ny <= 1) {
    double range = variogram.GetRangeX();
    pad.push_back(FindGaussianFieldPadding(variogram, nx, range, dx));
  }
  else if (nz <= 1) {
    double range_x = std::max(variogram.GetRangeX(), variogram.GetRangeY());
    double range_y = range_x;
    if (variogram.GetAzimuthAngle() == 0.0) {
      range_y = variogram.GetRangeY();
    }
    pad.push_back(FindGaussianFieldPadding(variogram, nx, range_x, dx));
    pad.push_back(FindGaussianFieldPadding(variogram, ny, range_y, dy));
  }
  else {
    double range_x, range_y, range_z;
    range_x = std::max(variogram.GetRangeX(), variogram.GetRangeY());
    range_y = range_x;
    if (variogram.GetAzimuthAngle() == 0.0) {
      range_y = variogram.GetRangeY();
    }
    range_z = variogram.GetRangeZ();
    pad.push_back(FindGaussianFieldPadding(variogram, nx, range_x, dx));
    pad.push_back(FindGaussianFieldPadding(variogram, ny, range_y, dy));
    pad.push_back(FindGaussianFieldPadding(variogram, nz, range_z, dz));
  }
  return pad;
}


/****************************************************************************************/
/* Implementations                                                                      */
/****************************************************************************************/

// Simulation of multiple fields with the same covariance function.
void NRLib::Simulate3DGaussianField(const Variogram              & variogram,
                                    size_t                         nx,
                                    double                         dx,
                                    size_t                         ny,
                                    double                         dy,
                                    size_t                         nz,
                                    double                         dz,
                                    int                            n_fields,
                                    std::vector<Grid<double> > &   grid_out,
                                    int                            padding_x,
                                    int                            padding_y,
                                    int                            padding_z,
                                    double                         scaling_x,
                                    double                         scaling_y,
                                    double                         scaling_z)
{
  std::vector<size_t> default_padding = FindNDimPadding(variogram,
                                                        nx,
                                                        dx,
                                                        ny,
                                                        dy,
                                                        nz,
                                                        dz);
  // This is the desired padding, but may not be the actual of the
  // FFT grid. See below.
  size_t desired_padding_x = (padding_x < 0) ? default_padding[0] : padding_x;
  size_t desired_padding_y = (padding_y < 0) ? default_padding[1] : padding_y;
  size_t desired_padding_z = (padding_z < 0) ? default_padding[2] : padding_z;

  FFTGrid3D<double> fftgrid(nx, ny, nz, desired_padding_x, desired_padding_y, desired_padding_z, true);

  // Get the total grid size after the grid is created. This is not necessarily the
  // same as nx + desired_padding_x. FFTGrid3D may add even more padding so that the
  // total grid size is more favorable for the FFT implementation.
  size_t nx_tot = fftgrid.GetNItot();
  size_t ny_tot = fftgrid.GetNJtot();
  size_t nz_tot = fftgrid.GetNKtot();

  // Covariance grid.
  Grid<double> cov = FFTCovGrid3D(variogram,
                                  static_cast<int>(nx_tot),
                                  dx,
                                  static_cast<int>(ny_tot),
                                  dy,
                                  static_cast<int>(nz_tot),
                                  dz,
                                  scaling_x,
                                  scaling_y,
                                  scaling_z).GetCov();

  FFTGrid3D<double> filter(nx,
                           ny,
                           nz,
                           desired_padding_x,
                           desired_padding_y,
                           desired_padding_z,
                           false);


  filter.Initialize(cov);
  filter.DoFFT();
  // Convolve with covariance grid.
  for (size_t i = 0; i < filter.GetComplexNI()*filter.GetComplexNJ()*filter.GetComplexNK(); i++) {
    filter.ComplexData()[i].real(std::max(filter.ComplexData()[i].real(), 0.0));
    filter.ComplexData()[i].imag(0.0);
    filter.ComplexData()[i] = std::sqrt(filter.ComplexData()[i]);
  }

  // Grid with white noice.
  Grid<double> noise(nx_tot, ny_tot, nz_tot);

  ////if (seed == -999)
  ////  seed = NRLib::Random::DrawUint32();
  //// This is done to be able to do multithreading
  ////NRLib::RandomGenerator random;
  //// random.Initialize(seed);
  //if (rg == NULL) {
  //  rg = new RandomGenerator();
  //  rg->Initialize(NRLib::Random::DrawUint32());
  //}
  for (int m = 0; m < n_fields; m++) {
    for (size_t i = 0; i < nx_tot; i++)
      for (size_t j = 0; j < ny_tot; j++)
        for (size_t k = 0; k < nz_tot; k++)
          noise(i, j, k) = NRLib::Random::Norm01();

    fftgrid.Initialize(noise);

    fftgrid.DoFFT();
    for (size_t i = 0; i < filter.GetComplexNI()*filter.GetComplexNJ()*filter.GetComplexNK(); i++)
      fftgrid.ComplexData()[i] *= filter.ComplexData()[i];

    fftgrid.DoInverseFFT();
    grid_out.push_back(fftgrid.GetRealGrid());
  }
}


void NRLib::Simulate2DGaussianField(const Variogram& variogram,
                                    size_t nx, double dx,
                                    size_t ny, double dy,
                                    // double padding_fraction,
                                    // bool   user_defined_padding,
                                    Grid2D<double> & grid_out)
{
  RandomGenerator * rg = NULL;
  try {
    unsigned long seed = Random::GetStartSeed();
    rg = new RandomGenerator(seed);
  }
  catch (std::exception) {
    // This will occur if NRLib::Random is not initilized. In this case,
    // use rg = NULL, which will be resolved by the other
    // Simulate2DGaussianField function
  }
  std::vector<Grid2D<double> > grids;
  Simulate2DGaussianField(variogram,
                          nx,
                          dx,
                          ny,
                          dy,
                          1,
                          grids,
                          rg);
  grid_out = grids[0];
}

// Simulation of multiple fields with the same covariance function.
void NRLib::Simulate2DGaussianField(const Variogram              & variogram,
                                    size_t                         nx,
                                    double                         dx,
                                    size_t                         ny,
                                    double                         dy,
                                    int                            n_fields,
                                    std::vector<Grid2D<double> > & grid_out,
                                    NRLib::RandomGenerator       * rg,
                                    int                            padding_x,
                                    int                            padding_y,
                                    double                         scaling_x,
                                    double                         scaling_y)
{
  std::vector<size_t> default_padding = FindNDimPadding(variogram,
                                                        nx,
                                                        dx,
                                                        ny,
                                                        dy);
  // This is the desired padding, but may not be the actual of the
  // FFT grid. See below.
  size_t desired_padding_x = (padding_x < 0) ? default_padding[0] : padding_x;
  size_t desired_padding_y = (padding_y < 0) ? default_padding[1] : padding_y;
  FFTGrid2D<double> fftgrid(nx, ny, desired_padding_x, desired_padding_y, true);

  // Get the total grid size after the grid is created. This is not necessarily the
  // same as nx + desired_padding_x. FFTGrid2D may add even more padding so that the
  // total grid size is more favorable for the FFT implementation.
  size_t nx_tot = fftgrid.GetNItot();
  size_t ny_tot = fftgrid.GetNJtot();

  // Covariance grid.
  Grid2D<double> cov = FFTCovGrid2D(variogram,
                                    static_cast<int>(nx_tot),
                                    dx,
                                    static_cast<int>(ny_tot),
                                    dy,
                                    scaling_x,
                                    scaling_y).GetCov();


  FFTGrid2D<double> filter(nx, ny, desired_padding_x, desired_padding_y, false);
  filter.Initialize(cov);
  filter.DoFFT();
  // Convolve with covariance grid.
  for (size_t i = 0; i < filter.GetComplexNI()*filter.GetComplexNJ(); i++) {
    filter.ComplexData()[i].real(std::max(filter.ComplexData()[i].real(), 0.0));
    filter.ComplexData()[i].imag(0.0);
    filter.ComplexData()[i] = std::sqrt(filter.ComplexData()[i]);
  }

  // Grid with white noice.
  Grid2D<double> noise(nx_tot,ny_tot);

  //if (seed == -999)
  //  seed = NRLib::Random::DrawUint32();
  // This is done to be able to do multithreading
  //NRLib::RandomGenerator random;
 // random.Initialize(seed);
  if(rg == NULL) {
    rg = new RandomGenerator();
    rg->Initialize(NRLib::Random::DrawUint32());
  }
  for (int k = 0; k < n_fields; k++) {
    for (size_t i = 0; i < nx_tot; i++)
      for (size_t j = 0; j < ny_tot; j++)
        noise(i,j) = rg->Norm01();

    fftgrid.Initialize(noise);

    fftgrid.DoFFT();
    for(size_t i = 0; i < filter.GetComplexNI()*filter.GetComplexNJ(); i++)
      fftgrid.ComplexData()[i] *= filter.ComplexData()[i];

    fftgrid.DoInverseFFT();
    grid_out.push_back(fftgrid.GetRealGrid());
  }
}

void
NRLib::Simulate1DGaussianField(const Variogram       & variogram,
                               size_t                  nx,
                               double                  dx,
                               std::vector<double>   & grid_out,
                               NRLib::RandomGenerator *rg,
                               int                     padding,
                               double                  scaling_x)
{
  std::vector<size_t> default_padding = FindNDimPadding(variogram,
                                                        nx,
                                                        dx);
  size_t nx_pad = (padding < 0) ? default_padding[0] : padding;

  // Find a favorable grid size (nx + padding) for the FFT implementation
  size_t nxp = NRLib::FindNewSizeWithPadding(nx + nx_pad);

  std::vector<double> cov = FFTCovGrid1D(variogram, static_cast<int>(nxp), dx, scaling_x).GetCov();

  if(rg == NULL) {
    rg = new RandomGenerator();
    rg->Initialize(NRLib::Random::DrawUint32());
  }
  std::vector<double> noise(nxp);
  for(size_t i = 0; i < nxp; i++)
    noise[i] = rg->Norm01();
  std::vector<std::complex<double> > cov_fft;
  std::vector<std::complex<double> > noise_fft;
  NRLib::ComputeFFT1D(cov, cov_fft, false,0);
  NRLib::ComputeFFT1D(noise, noise_fft, true,0);
  std::vector<std::complex<double> > convolve(cov_fft.size());

  for(size_t i = 0; i < cov_fft.size(); i++){
    cov_fft[i].real(std::max(cov_fft[i].real(), 0.0));
    cov_fft[i].imag(0.0);
    cov_fft[i] = std::sqrt(cov_fft[i]);
  }

  for(size_t i = 0; i < cov_fft.size(); i++)
    convolve[i] = cov_fft[i]*noise_fft[i];

  std::vector<double> tmp(nxp);

  NRLib::ComputeFFTInv1D(convolve, tmp, true);

  for(size_t i = 0; i < grid_out.size(); i++)
    grid_out[i] = tmp[i];
}


/*
void
NRLib::Simulate1DGaussianField(NRLib::Matrix cov_in,
                               size_t nx,
                               std::vector<double> & grid_out)
{
 // double range = variogram.GetRangeX();
 // size_t nx_pad = std::max(static_cast<size_t>(4.0 * range / dx), 2*nx) - nx;
  size_t nx_pad = 2*nx;
  std::vector<double> cov(nx_pad);
 // size_t nxm = (nx_pad+1)/2;
  for(size_t i = 0; i < nx; i++){
    cov[i] = cov_in(static_cast<int> (i),0);
  }
  for(size_t i=nx; i < nx_pad; i++){
    cov[i] = cov_in(static_cast<int> (nx_pad-i),0);
  }

  std::vector<double> noise(2*nx_pad);
  for(size_t i = 0; i < 2*nx_pad; i++)
    noise[i] = NRLib::Random::Norm01();
  std::vector<std::complex<double> > cov_fft;
  std::vector<std::complex<double> > noise_fft;
  NRLib::ComputeFFT1D(cov, cov_fft, true);
  NRLib::ComputeFFT1D(noise, noise_fft, true);
  std::vector<std::complex<double> > convolve(cov_fft.size());

  for(size_t i = 0; i < cov_fft.size(); i++)
    convolve[i] = std::sqrt(cov_fft[i])*noise_fft[i];


  NRLib::ComputeFFTInv1D(convolve, grid_out, true);
}
*/
