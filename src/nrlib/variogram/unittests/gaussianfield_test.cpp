/// Unit tests for gaussian field simulation

#include <nrlib/grid/grid2d.hpp>
#include <nrlib/random/random.hpp>
#include <nrlib/variogram/gaussianfield.hpp>
#include <nrlib/variogram/variogram.hpp>

#include <boost/test/unit_test.hpp>

using namespace NRLib;

BOOST_AUTO_TEST_SUITE( TestGaussianField )

BOOST_AUTO_TEST_CASE( Sim2dComparison )
{
  Variogram * v = Variogram::Create(Variogram::EXPONENTIAL, 1.5, 1000.0, 500.0, 250.0);
  Grid2D<double> field;
  std::vector<Grid2D<double> > fields;
  Random::Initialize(123L);
  Simulate2DGaussianField(*v, 100, 20, 100, 20, field);
  unsigned long seed = Random::GetStartSeed();
  RandomGenerator * rg = new RandomGenerator(seed);
  Simulate2DGaussianField(*v, 100, 20, 100, 20, 1, fields, rg);
  delete rg;
  delete v;

  BOOST_TEST(field.GetStorage().size() == fields[0].GetStorage().size());
  // Check enough values to perform a valid comparison, but not
  // so many that it is computationally demanding.
  for (size_t i = 0; i < field.GetStorage().size(); i+=73) {
    BOOST_CHECK_CLOSE(field.GetStorage()[i], fields[0].GetStorage()[i], 1e-6);
  }
}

BOOST_AUTO_TEST_CASE( Sim2dValues )
{
  Variogram * v = Variogram::Create(Variogram::EXPONENTIAL, 1.5, 1000.0, 500.0, 250.0);
  std::vector<Grid2D<double> > fields;
  RandomGenerator * rg = new RandomGenerator(321);
  Simulate2DGaussianField(*v, 757, 20, 757, 20, 1, fields, rg);
  delete rg;
  delete v;
  const std::vector<double> & values = fields[0].GetStorage();
  // Values retrieved on a Win7 64-bit machine
  // Any lower tolerance may cause the closeness check
  // to fail.
  BOOST_CHECK_CLOSE(values[1] , 0.28061384793803246, 1e-11);
  BOOST_CHECK_CLOSE(values[11], 0.13965269545564776, 1e-11);
  BOOST_CHECK_CLOSE(values[33], 0.27412175512645326, 1e-11);
  BOOST_CHECK_CLOSE(values[77], 1.3560438495926139 , 1e-11);
}

BOOST_AUTO_TEST_SUITE_END()
