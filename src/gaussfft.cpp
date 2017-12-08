#include "gaussfft.hpp"

//#include <chrono>
#include <iostream>

#include "nrlib/iotools/stringtools.hpp"
#include "nrlib/grid/grid.hpp"
#include "nrlib/grid/grid2d.hpp"
#include "nrlib/math/constants.hpp"
#include "nrlib/random/random.hpp"
#include "nrlib/variogram/variogram.hpp"
#include "nrlib/variogram/gaussianfield.hpp"

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
  std::vector<size_t> out;
  out.push_back(NRLib::FindGaussianFieldPadding(nx, variogram->GetRangeX(), dx));
  if (ny > 1) {
    out.push_back(NRLib::FindGaussianFieldPadding(ny, variogram->GetRangeY(), dy));
    if (nz > 1) {
      out.push_back(NRLib::FindGaussianFieldPadding(nz, variogram->GetRangeZ(), dz));
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
std::vector<double> GaussFFT::Simulate(NRLib::Variogram * variogram,
                                       size_t             nx,
                                       double             dx,
                                       size_t             ny,
                                       double             dy,
                                       size_t             nz,
                                       double             dz)
{
  return SimulateWithCustomPadding(variogram, nx, dx, ny, dy, nz, dz, -1, -1,-1);
}

/***********************************************************************************/
std::vector<double> GaussFFT::SimulateWithCustomPadding(NRLib::Variogram * variogram,
                                                        size_t             nx,
                                                        double             dx,
                                                        size_t             ny,
                                                        double             dy,
                                                        size_t             nz,
                                                        double             dz,
                                                        int                padding_x,
                                                        int                padding_y,
                                                        int                padding_z)
{
  try {
    NRLib::Random::GetStartSeed();
  }
  catch (NRLib::Exception e) {
    // NRLib::Random is not initialized yet. Use empty initializer:
    NRLib::Random::Initialize();
  }
  if (ny <= 1U || dy < 0.0) {
    return GaussFFT::Simulate1D(variogram, nx, dx, padding_x);
  }
  else if (nz <= 1U || dz < 0.0) {
    return GaussFFT::Simulate2D(variogram, nx, dx, ny, dy, padding_x, padding_y);
  }
  else {
    return GaussFFT::Simulate3D(variogram, nx, dx, ny, dy, nz, dz, padding_x, padding_y, padding_z);
  }
}

/********************************************************************/
std::vector<double> GaussFFT::Simulate1D(NRLib::Variogram * variogram,
                                         size_t             nx,
                                         double             dx,
                                         int                padding_x)
{
  std::vector<double> values;
  // Have to allocate memory (for some reason) before running the simulation
  values.resize(nx);
  NRLib::Simulate1DGaussianField(*variogram,
                                 nx,
                                 dx,
                                 values,
                                 NULL, // Will use NRLib::Random state
                                 padding_x);
  return values;
}

/********************************************************************/
std::vector<double> GaussFFT::Simulate2D(NRLib::Variogram * variogram,
                                         size_t             nx,
                                         double             dx,
                                         size_t             ny,
                                         double             dy,
                                         int                padding_x,
                                         int                padding_y)
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
                                 padding_y);
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
                                         int                padding_z)
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
                                 padding_z);
  return fields[0].GetStorage();
}
