#pragma once

#include <string>
#include "nrlib/grid/grid.hpp"

namespace NRLib {
class Variogram;
}

namespace GaussFFT {

std::string Quote();

NRLib::Variogram *
CreateVariogram(std::string type,
                double      range_x,
                double      range_y,
                double      range_z,
                double      azimuth_angle,
                double      dip_angle,
                double      power);

std::vector<double> Simulate(NRLib::Variogram * variogram,
                             size_t             nx,
                             double             dx,
                             size_t             ny,
                             double             dy,
                             size_t             nz,
                             double             dz);

std::vector<double> SimulateWithCustomPadding(NRLib::Variogram * variogram,
                                              size_t             nx,
                                              double             dx,
                                              size_t             ny,
                                              double             dy,
                                              size_t             nz,
                                              double             dz,
                                              int                padding_x,
                                              int                padding_y,
                                              int                padding_z);

std::vector<double> Simulate1D(NRLib::Variogram * variogram,
                               size_t             nx,
                               double             dx,
                               int                padding_x);

std::vector<double> Simulate2D(NRLib::Variogram * variogram,
                               size_t             nx,
                               double             dx,
                               size_t             ny,
                               double             dy,
                               int                padding_x,
                               int                padding_y);

std::vector<double> Simulate3D(NRLib::Variogram * variogram,
                               size_t             nx,
                               double             dx,
                               size_t             ny,
                               double             dy,
                               size_t             nz,
                               double             dz,
                               int                padding_x,
                               int                padding_y,
                               int                padding_z);
}
