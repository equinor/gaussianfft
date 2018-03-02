// $Id: gaussianfield.hpp 1756 2018-02-23 10:50:34Z vegard $

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

#ifndef NRLIB_VARIOGRAM_GAUSSIANFIELD_HPP
#define NRLIB_VARIOGRAM_GAUSSIANFIELD_HPP

#include <cstdlib>
#include <vector>
#include "../random/randomgenerator.hpp"

namespace NRLib {
  class Variogram;
  template <typename T> class Grid2D;
  template <typename T> class Grid;
  size_t              FindGaussianFieldPadding(const Variogram & variogram, size_t grid_size, double range, double step);
  std::vector<size_t> FindNDimPadding         (const Variogram & variogram,
                                               size_t            nx,
                                               double            dx,
                                               size_t            ny = 1,
                                               double            dy = -1,
                                               size_t            nz = 1,
                                               double            dz = -1);

  void Simulate3DGaussianField(const Variogram              & variogram,
                               size_t                         nx,
                               double                         dx,
                               size_t                         ny,
                               double                         dy,
                               size_t                         nz,
                               double                         dz,
                               int                            n_fields,
                               std::vector<Grid<double> > &   grid_out,
                               int                            padding_x = -1,
                               int                            padding_y = -1,
                               int                            padding_z = -1,
                               double                         scaling_x = 1.0,
                               double                         scaling_y = 1.0,
                               double                         scaling_z = 1.0);

  /// Simulate 2D Gaussian fields. variogram specifies the variogram and
  /// nx/y, dx/y specify the size. n_fields is the number of realizations
  /// rg can be used to control the RNG. padding_x/y can be used to
  /// provide a custom padding (advanced functionality). padding_x/y
  /// values that are negative will be set to a size that is large enough
  /// to avoid circular effects and ringing effects.
  void Simulate2DGaussianField(const Variogram &              variogram,
                               size_t                         nx,
                               double                         dx,
                               size_t                         ny,
                               double                         dy,
                               int                            n_fields,
                               std::vector<Grid2D<double> > & grid_out,
                               NRLib::RandomGenerator        *rg = NULL,
                               int                            padding_x = -1,
                               int                            padding_y = -1,
                               double                         scaling_x = 1.0,
                               double                         scaling_y = 1.0);

  void Simulate2DGaussianField(const Variogram& variogram,
                               size_t nx, double dx,
                               size_t ny, double dy,
                               // double padding_fraction,
                               // bool   user_defined_padding,
                               Grid2D<double> & grid_out);

  void Simulate1DGaussianField(const Variogram        & variogram,
                               size_t                   nx,
                               double                   dx,
                               std::vector<double>    & grid_out,
                               NRLib::RandomGenerator * rg = NULL,
                               int                      padding = -1,
                               double                   scaling_x = 1.0);

 // void Simulate1DGaussianField(NRLib::Matrix cov_in,
 //                              size_t nx,
//                               std::vector<double> & grid_out);

} // namespace NRLib

#endif // NRLIB_VARIOGRAM_GAUSSIANFIELD_HPP
