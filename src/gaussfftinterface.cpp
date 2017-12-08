#define BOOST_PYTHON_STATIC_LIB

#include <boost/python.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>

// May want to reintroduce this later:
// #include <boost/python/numpy.hpp>

#include "gaussfft.hpp"

#include "nrlib/variogram/variogram.hpp"
#include "nrlib/random/random.hpp"

namespace bp = boost::python;

/**********************************************/
/* Docstrings                                 */
/**********************************************/

const std::string padding_docstring =
  "\n"
  "Function for determining the grid size after padding in order to assess the\n"
  "complexity of the problem. Returns bindings to a vector with up to three elements\n"
  "with the number of grid cells after the grid has been padded. Signature is the\n"
  "same as nrlib.simulate.\n"
  "\n"
  "Examples\n"
  "--------\n"
  ">>> v = nrlib.variogram('spherical', 250.0, 125.0)\n"
  ">>> nx, ny, dx, dy = 100, 100, 10.0, 10.0\n"
  ">>> list(nrlib.simulation_size(v, nx, dx, ny, dy))\n"
  "[25, 12]\n"
;

const std::string variogram_docstring =
  "\n"
  "Factory function for creating a particular variogram. The variogram is always\n"
  "defined in three directions, but for simulation in fewer dimensions than three,\n"
  "only the corresponding number of directions are used.\n"
  "\n"
  "Parameters\n"
  "----------\n"
  "type: string\n"
  "    A string representing the type of variogram. The following types are supported:\n"
  "    gaussian, exponential, general_exponential, spherical, matern32, matern52,\n"
  "    matern72 and constant.\n"
  "main_range: float\n"
  "    Range of the variogram in the main direction.\n"
  "perp_range, depth_range: floats, optional\n"
  "    Parameters representing the range of the variogram in the two directions\n"
  "    perpendicular to main_range. If any of these are zero, the default is to set\n"
  "    the value to the same as main_range.\n"
  "azimuth: float, optional\n"
  "    Lateral orientation of the variogram in degrees. Default is 0.0.\n"
  "dip: float, optional\n"
  "    Dip direction of the variogram in degrees. Default is 0.0\n"
  "power: float, optional\n"
  "    Power of the exponent for the general_exponential variogram, which is the only\n"
  "    variogram type this is used for. Default is 1.5.\n"
  "\n"
  "Returns\n"
  "-------\n"
  "out: Variogram\n"
  "    An instance of the class nrlib.Variogram.\n"
  "\n"
  "Examples\n"
  "--------\n"
  ">>> nrlib.variogram('gaussian', 1000.0)\n"
  "\n"
  "Specifying dip\n"
  "\n"
  ">>> nrlib.variogram('matern52', 1000.0, dip=45.0)\n"
  "\n"
  "Multiple directions\n"
  "\n"
  ">>> nrlib.variogram('general_exponential', 1000.0, 500.0, 250.0, power=1.8)\n"
;

const std::string simulate_docstring =
  "\n"
  "Simulates a Gaussian random field with the corresponding variogram in one, two or\n"
  "three dimensions. The random generator seed may be set by using nrlib.seed.\n"
  "\n"
  "Parameters\n"
  "----------\n"
  "variogram: nrlib.Variogram\n"
  "    An instance of nrlib.Variogram (see nrlib.variogram).\n"
  "nx, ny, nz: int\n"
  "    Grid size of the simulated field. Only nx is required. Setting ny and/or nz to\n"
  "    a value less than or equal to 1 reduces the dimension. Default is ny = 1 and \n"
  "    nz = 1.\n"
  "dx, dy, dz: float\n"
  "    Grid resolution in x, y and z directions. dx is always required. dy and dz are\n"
  "    required if respectively ny and nz are greater than 1.\n"
  "\n"
  "Returns\n"
  "-------\n"
  "out: DoubleVector\n"
  "    Bindings to a C++ vector of double precision floats. The vector is iterable\n"
  "    and can thus be transformed into a numpy array directly. The result is always\n"
  "    a 1D vector, using Fortran ordering if the simulation is multi-dimensional.\n"
  "\n"
  "Examples\n"
  "--------\n"
  ">>> v = nrlib.variogram('gaussian', 250.0, 125.0)\n"
  ">>> nx, dx = 10, 100.0\n"
  ">>> z = nrlib.simulate(v, nx, dx)\n"
  ">>> np.array(z)\n"
  "array([-1.29924289, -1.51172913, -1.2935657 , -0.80779427,  0.22217236,\n"
  "        1.26740091,  0.66094991, -0.77396656,  0.01523847,  0.44392584])\n"
  "\n"
  "Multi-dimensional simulation\n"
  "\n"
  ">>> nx, ny = 100, 200\n"
  ">>> dx, dy = 10.0, 5.0\n"
  ">>> z = nrlib.simulate(v, nx, dx, ny, dy)\n"
  ">>> z_np = np.array(z).reshape((nx, ny), order='F')\n"
  ">>> z_np.shape\n"
  "(100,200)\n"
;

/**********************************************/
/**********************************************/
/**********************************************/

BOOST_PYTHON_MODULE(nrlib)
{
  bp::class_<std::vector<double> >("DoubleVector")
    .def(bp::vector_indexing_suite< std::vector<double> >())
  ;
  bp::class_<std::vector<size_t> >("SizeTVector")
    .def(bp::vector_indexing_suite< std::vector<size_t> >())
    ;
  bp::def("quote",&GaussFFT::Quote);

  //
  // Variogram class
  //
  {
    double(NRLib::Variogram::*ptr1)(double)                 const = &NRLib::Variogram::GetCorr;
    double(NRLib::Variogram::*ptr2)(double, double)         const = &NRLib::Variogram::GetCorr;
    double(NRLib::Variogram::*ptr3)(double, double, double) const = &NRLib::Variogram::GetCorr;
    bp::class_<NRLib::Variogram, boost::noncopyable>("Variogram", bp::no_init)
      .def("corr", ptr1)
      .def("corr", ptr2)
      .def("corr", ptr3)
    ;
  }

  //
  // NRLib::Random
  //
  {
    void(*ptr)(unsigned long) = &NRLib::Random::Initialize;
    bp::def("seed", ptr);
  }

  //
  // Padding
  //
  bp::def("simulation_size", &GaussFFT::FindGridSizeAfterPadding,
    (
      bp::arg("variogram"),
      bp::arg("nx"),
      bp::arg("dx"),
      bp::arg("ny") = 1U,
      bp::arg("dy") = -1.0,
      bp::arg("nz") = 1U,
      bp::arg("dz") = -1.0
    ),
    padding_docstring.c_str()
  );

  //
  // Variogram factory function
  //
  bp::def("variogram", &GaussFFT::CreateVariogram,
    (
      bp::arg("type"),
      bp::arg("main_range"),
      bp::arg("perp_range")=-1.0,
      bp::arg("depth_range")=-1.0,
      bp::arg("azimuth")=0.0,
      bp::arg("dip")=0.0,
      // bp::arg("sd")=1.0,
      bp::arg("power")=1.5
    ),
    bp::return_value_policy<bp::manage_new_object>(),
    variogram_docstring.c_str()
  );
  //
  // Simulate core function
  //
  bp::def("simulate", &GaussFFT::Simulate,
    (
      bp::arg("variogram"),
      bp::arg("nx"),
      bp::arg("dx"),
      bp::arg("ny")=1U,
      bp::arg("dy")=-1.0,
      bp::arg("nz")=1U,
      bp::arg("dz")=-1.0
    ),
    simulate_docstring.c_str()
  );

  /******************* Advanced *******************/
  // Boilerplate module stuff (http://isolation-nation.blogspot.no/2008/09/packages-in-python-extension-modules.html)
  bp::object the_module(
    bp::handle<>(bp::borrowed(PyImport_AddModule("nrlib.advanced")))
  );
  bp::scope().attr("advanced") = the_module;
  bp::scope the_scope = the_module;
  //
  // Simulate core function
  //
  bp::def("simulate", &GaussFFT::SimulateWithCustomPadding,
    (
      bp::arg("variogram"),
      bp::arg("nx"),
      bp::arg("dx"),
      bp::arg("ny") = 1U,
      bp::arg("dy") = -1.0,
      bp::arg("nz") = 1U,
      bp::arg("dz") = -1.0,
      bp::arg("padx") = -1,
      bp::arg("pady") = -1,
      bp::arg("padz") = -1
    )
  );
}
