#include "gaussfft.hpp"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <iostream>

#include "nrlib/iotools/stringtools.hpp"
#include "nrlib/exception/exception.hpp"
#include "nrlib/grid/grid.hpp"
#include "nrlib/grid/grid2d.hpp"
#include "nrlib/math/constants.hpp"
#include "nrlib/random/random.hpp"
#include "nrlib/variogram/variogram.hpp"
#include "nrlib/variogram/gaussianfield.hpp"

namespace py = pybind11;

/***************************/
std::string GaussFFT::Quote()
{
  return "Arc, amplitude, and curvature sustain a similar relation to each other as time, motion, and velocity, or as volume, mass, and density.";
}

/**********************************************************************************/
std::vector<size_t> GaussFFT::FindGridSizeAfterPadding(NRLib::Variogram * variogram,
                                                       size_t             nx,
                                                       double             dx,
                                                       size_t             ny,
                                                       double             dy,
                                                       size_t             nz,
                                                       double             dz)
{
  std::vector<size_t> out = NRLib::FindNDimPadding(*variogram,
                                                   nx,
                                                   dx,
                                                   ny,
                                                   dy,
                                                   nz,
                                                   dz);
  // Add simulation grid size to that output reflects final grid size
  // and not padding only
  out[0] += nx;
  if (out.size() > 1) {
    out[1] += ny;
    if (out.size() > 2) {
      out[2] += nz;
    }
  }
  return out;
}

/*********************************************************************/
NRLib::Variogram * GaussFFT::CreateVariogram(const std::string & type,
                                             double              range_x,
                                             double              range_y,
                                             double              range_z,
                                             double              azimuth_angle,
                                             double              dip_angle,
                                             double              power)
{
  if (range_y < 0.0)
    range_y = range_x;
  if (range_z < 0.0)
    range_z = range_x;

  azimuth_angle *= NRLib::Degree;
  dip_angle *= NRLib::Degree;

  NRLib::Variogram::Type t;
  std::string utype = NRLib::Uppercase(type);
  if (utype == "CONSTANT")
    t = NRLib::Variogram::CONSTANT;
  else if (utype == "EXPONENTIAL")
    t = NRLib::Variogram::EXPONENTIAL;
  else if (utype == "GAUSSIAN")
    t = NRLib::Variogram::GAUSSIAN;
  else if (utype == "GENERAL_EXPONENTIAL")
    t = NRLib::Variogram::GENERAL_EXPONENTIAL;
  else if (utype == "MATERN32")
    t = NRLib::Variogram::MATERN32;
  else if (utype == "MATERN52")
    t = NRLib::Variogram::MATERN52;
  else if (utype == "MATERN72")
    t = NRLib::Variogram::MATERN72;
  else if (utype == "SPHERICAL")
    t = NRLib::Variogram::SPHERICAL;
  else
    t = NRLib::Variogram::SPHERICAL;

  return NRLib::Variogram::Create(t, power, range_x, range_y, range_z, azimuth_angle, dip_angle, 1.0);
}

/******************************************************************/
py::array_t<double> GaussFFT::Simulate(NRLib::Variogram * variogram,
                                       size_t             nx,
                                       double             dx,
                                       size_t             ny,
                                       double             dy,
                                       size_t             nz,
                                       double             dz)
{
  return SimulateWithAdvancedSettings(variogram, nx, dx, ny, dy, nz, dz, -1, -1,-1, 1.0, 1.0, 1.0);
}

/***********************************************************************************/
py::array_t<double> GaussFFT::SimulateWithAdvancedSettings(NRLib::Variogram * variogram,
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
                                                           double             scaling_z)
{
  try {
    NRLib::Random::GetStartSeed();
  }
  catch (NRLib::Exception e) {
    // NRLib::Random is not initialized yet. Use empty initializer:
    NRLib::Random::Initialize();
  }
  std::vector<double> result;
  if (ny <= 1U || dy < 0.0) {
    result = GaussFFT::Simulate1D(variogram, nx, dx,                 padding_x,                       scaling_x                      );
  }
  else if (nz <= 1U || dz < 0.0) {
    result = GaussFFT::Simulate2D(variogram, nx, dx, ny, dy,         padding_x, padding_y,            scaling_x, scaling_y           );
  }
  else {
    result = GaussFFT::Simulate3D(variogram, nx, dx, ny, dy, nz, dz, padding_x, padding_y, padding_z, scaling_x, scaling_y, scaling_z);
  }

  py::array_t<double> np_result = py::cast(result);
  return np_result;
}

/********************************************************************/
std::vector<double> GaussFFT::Simulate1D(NRLib::Variogram * variogram,
                                         size_t             nx,
                                         double             dx,
                                         int                padding_x,
                                         double             scaling_x)
{
  std::vector<double> values;
  // Have to allocate memory (for some reason) before running the simulation
  values.resize(nx);
  NRLib::Simulate1DGaussianField(*variogram,
                                 nx,
                                 dx,
                                 values,
                                 NULL, // Will use NRLib::Random state
                                 padding_x,
                                 scaling_x);
  return values;
}

/********************************************************************/
std::vector<double> GaussFFT::Simulate2D(NRLib::Variogram * variogram,
                                         size_t             nx,
                                         double             dx,
                                         size_t             ny,
                                         double             dy,
                                         int                padding_x,
                                         int                padding_y,
                                         double             scaling_x,
                                         double             scaling_y)
{
  std::vector<NRLib::Grid2D<double> > fields;
  NRLib::Simulate2DGaussianField(*variogram,
                                 nx,
                                 dx,
                                 ny,
                                 dy,
                                 1,
                                 fields,
                                 NULL, // Will use NRLib::Random state
                                 padding_x,
                                 padding_y,
                                 scaling_x,
                                 scaling_y);
  return fields[0].GetStorage();
}

/*********************************************************************/
std::vector<double> GaussFFT::Simulate3D(NRLib::Variogram * variogram,
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
                                         double             scaling_z)
{
  std::vector<NRLib::Grid<double> > fields;
  NRLib::Simulate3DGaussianField(*variogram,
                                 nx,
                                 dx,
                                 ny,
                                 dy,
                                 nz,
                                 dz,
                                 1,
                                 fields,
                                 padding_x,
                                 padding_y,
                                 padding_z,
                                 scaling_x,
                                 scaling_y,
                                 scaling_z);
  return fields[0].GetStorage();
}
