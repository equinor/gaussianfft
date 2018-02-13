/// Unit tests for gaussian field simulation

#include <nrlib/grid/grid2d.hpp>
#include <nrlib/variogram/variogram.hpp>
#include <nrlib/variogram/fftcovgrid.hpp>

#include <boost/test/unit_test.hpp>

using namespace NRLib;

BOOST_AUTO_TEST_SUITE( TestFFTCovGrid )

BOOST_AUTO_TEST_CASE( BasicFFTCovGrid1D )
{
  Variogram * v = Variogram::Create(Variogram::EXPONENTIAL, 1.5, 500.0);
  FFTCovGrid1D cg(*v, 100, 10.0);
  const std::vector<double> & grid = cg.GetCov();

  // Check known values (approximately)
  BOOST_CHECK_CLOSE(grid[50], 0.05, 5.0);
  BOOST_CHECK_CLOSE(grid[0] , 1.00, 1e-6);

  // Check symmetry
  BOOST_CHECK_CLOSE(grid[99], grid[1], 1e-6);
}

BOOST_AUTO_TEST_CASE( SmoothenedFFTCovGrid1D )
{
  Variogram * v = Variogram::Create(Variogram::EXPONENTIAL, 1.5, 500.0);
  FFTCovGrid1D cg(*v, 100, 10.0, 0.33);
  const std::vector<double> & grid = cg.GetCov();

  // Check known values (approximately)
  BOOST_CHECK_CLOSE(grid[50], 0.05 * 0.33, 5.0);

  // Check symmetry
  BOOST_CHECK_CLOSE(grid[0] , 1.0    , 1e-6);
  BOOST_CHECK_CLOSE(grid[99], grid[1], 1e-6);
}

BOOST_AUTO_TEST_CASE( BasicFFTCovGrid2D )
{
  Variogram * v = Variogram::Create(Variogram::EXPONENTIAL, 1.5, 500.0, 500.0);

  FFTCovGrid2D cg(*v, 100, 10.0, 100, 10.0);

  const NRLib::Grid2D<double> & grid = cg.GetCov();

  // Check known values (approximately)
  BOOST_CHECK_CLOSE(grid(50, 0), 0.05, 5.0);
  BOOST_CHECK_CLOSE(grid(0, 50), 0.05, 5.0);
  BOOST_CHECK_CLOSE(grid(0 , 0), 1.00, 1e-6);

  // Check symmetry
  BOOST_CHECK_CLOSE(grid(0 , 99), grid(0, 1), 1e-6);
  BOOST_CHECK_CLOSE(grid(99, 0 ), grid(1, 0), 1e-6);
  BOOST_CHECK_CLOSE(grid(99, 99), grid(1, 1), 1e-6);
}

BOOST_AUTO_TEST_CASE( SmoothenedFFTCovGrid2D )
{
  Variogram * v = Variogram::Create(Variogram::EXPONENTIAL, 1.5, 500.0, 500.0);

  FFTCovGrid2D cg(*v, 100, 10.0, 100, 10.0, 0.33, 0.33);

  const NRLib::Grid2D<double> & grid = cg.GetCov();

  // Check known values (approximately)
  BOOST_CHECK_CLOSE(grid(50, 0), 0.05 * 0.33, 5.0);
  BOOST_CHECK_CLOSE(grid(0, 50), 0.05 * 0.33, 5.0);

  // Check symmetry
  BOOST_CHECK_CLOSE(grid(0, 0)  , 1.0       , 1e-6);
  BOOST_CHECK_CLOSE(grid(0 , 99), grid(0, 1), 1e-6);
  BOOST_CHECK_CLOSE(grid(99, 0 ), grid(1, 0), 1e-6);
  BOOST_CHECK_CLOSE(grid(99, 99), grid(1, 1), 1e-6);
}

BOOST_AUTO_TEST_CASE( BasicFFTCovGrid3D )
{
  Variogram * v = Variogram::Create(Variogram::EXPONENTIAL, 1.5, 500.0, 500.0, 500.0);
  FFTCovGrid3D cg(*v, 44, 1000.0/44, 44, 1000.0/44, 44, 1000.0/44);
  const NRLib::Grid<double> & grid = cg.GetCov();

  // Check known values (approximately)
  BOOST_CHECK_CLOSE(grid(22,  0,  0), 0.05, 5.0);
  BOOST_CHECK_CLOSE(grid( 0, 22,  0), 0.05, 5.0);
  BOOST_CHECK_CLOSE(grid( 0,  0, 22), 0.05, 5.0);
  BOOST_CHECK_CLOSE(grid( 0,  0,  0), 1.00, 1e-6);

  // Check symmetry
  BOOST_CHECK_CLOSE(grid(43, 0,  0), grid(1, 0, 0), 1e-6);
  BOOST_CHECK_CLOSE(grid(0, 43,  0), grid(0, 1, 0), 1e-6);
  BOOST_CHECK_CLOSE(grid(0,  0, 43), grid(0, 0, 1), 1e-6);
}

BOOST_AUTO_TEST_CASE( SmoothenedFFTCovGrid3D )
{
  Variogram * v = Variogram::Create(Variogram::EXPONENTIAL, 1.5, 500.0, 500.0, 500.0);
  FFTCovGrid3D cg(*v, 44, 1000.0 / 44, 44, 1000.0 / 44, 44, 1000.0 / 44, 0.33, 0.33, 0.33);
  const NRLib::Grid<double> & grid = cg.GetCov();

  // Check known values (approximately)
  BOOST_CHECK_CLOSE(grid(22,  0,  0), 0.05 * 0.33, 5.0);
  BOOST_CHECK_CLOSE(grid( 0, 22,  0), 0.05 * 0.33, 5.0);
  BOOST_CHECK_CLOSE(grid( 0,  0, 22), 0.05 * 0.33, 5.0);
  BOOST_CHECK_CLOSE(grid( 0,  0,  0),        1.00, 1e-6);

  // Check symmetry
  BOOST_CHECK_CLOSE(grid(43, 0,  0), grid(1, 0, 0), 1e-6);
  BOOST_CHECK_CLOSE(grid(0, 43,  0), grid(0, 1, 0), 1e-6);
  BOOST_CHECK_CLOSE(grid(0,  0, 43), grid(0, 0, 1), 1e-6);
}

BOOST_AUTO_TEST_SUITE_END()
