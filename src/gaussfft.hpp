#pragma once

#include <string>
#include "nrlib/grid/grid.hpp"
#include "nrlib/variogram/variogram.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

namespace GaussFFT {

std::string Quote();

std::vector<size_t> FindGridSizeAfterPadding(NRLib::Variogram * variogram,
                                             size_t             nx,
                                             double             dx,
                                             size_t             ny,
                                             double             dy,
                                             size_t             nz,
                                             double             dz);

NRLib::Variogram *
CreateVariogram(const std::string & type,
                double      range_x,
                double      range_y,
                double      range_z,
                double      azimuth_angle,
                double      dip_angle,
                double      power);

py::array_t<double>Simulate(NRLib::Variogram * variogram,
                                       size_t             nx,
                                       double             dx,
                                       size_t             ny,
                                       double             dy,
                                       size_t             nz,
                                       double             dz);

py::array_t<double> SimulateWithAdvancedSettings(NRLib::Variogram * variogram,
                                                           size_t             nx,
                                                           double             dx,
                                                           size_t             ny,
                                                           double             dy,
                                                           size_t             nz,
                                                           double             dz,
                                                           int                padding_x,
                                                           int                padding_y,
                                                           int                padding_z,
                                                           double             scaling_x,
                                                           double             scaling_y,
                                                           double             scaling_z);

std::vector<double> Simulate1D(NRLib::Variogram * variogram,
                               size_t             nx,
                               double             dx,
                               int                padding_x,
                               double             scaling_x);

std::vector<double> Simulate2D(NRLib::Variogram * variogram,
                               size_t             nx,
                               double             dx,
                               size_t             ny,
                               double             dy,
                               int                padding_x,
                               int                padding_y,
                               double             scaling_x,
                               double             scaling_y);

std::vector<double> Simulate3D(NRLib::Variogram * variogram,
                               size_t             nx,
                               double             dx,
                               size_t             ny,
                               double             dy,
                               size_t             nz,
                               double             dz,
                               int                padding_x,
                               int                padding_y,
                               int                padding_z,
                               double             scaling_x,
                               double             scaling_y,
                               double             scaling_z);
}
