#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "gaussfft.hpp"

#include "nrlib/variogram/variogram.hpp"
#include "nrlib/random/random.hpp"

namespace py = pybind11;

/**********************************************/
/* Docstrings                                 */
/**********************************************/

const std::string set_seed_docstring =
  ""
  "Sets the current simulation seed. If this has not been set when calling\n"
  "gaussianfft.simulate, it is set to the current time with second precision. Be wary of\n"
  "the latter, in particular if gaussianfft is used in a parallel-processing context.\n"
  "\n"
  "Examples\n"
  "--------\n"
  ">>> gaussianfft.seed(123)\n"
;

const std::string get_seed_docstring =
  ""
  "Gets the current simulation seed. Throws RunTimeError if the seed has not been set\n"
  "yet.\n"
  "\n"
  "Examples\n"
  "--------\n"
  ">>> gaussianfft.seed(123)\n"
  ">>> gaussianfft.seed()\n"
  "123\n"
;

const std::string padding_docstring =
  "\n"
  "Function for determining the grid size after padding in order to assess the\n"
  "complexity of the problem. Returns bindings to a vector with up to three elements\n"
  "with the number of grid cells after the grid has been padded. Signature is the\n"
  "same as gaussianfft.simulate.\n"
  "\n"
  "Examples\n"
  "--------\n"
  ">>> v = gaussianfft.variogram('spherical', 250.0, 125.0)\n"
  ">>> nx, ny, dx, dy = 100, 100, 10.0, 10.0\n"
  ">>> list(gaussianfft.simulation_size(v, nx, dx, ny, dy))\n"
  "[126, 113]\n"
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
  "    An instance of the class gaussianfft.Variogram.\n"
  "\n"
  "Examples\n"
  "--------\n"
  ">>> gaussianfft.variogram('gaussian', 1000.0)\n"
  "\n"
  "Specifying dip\n"
  "\n"
  ">>> gaussianfft.variogram('matern52', 1000.0, dip=45.0)\n"
  "\n"
  "Multiple directions\n"
  "\n"
  ">>> gaussianfft.variogram('general_exponential', 1000.0, 500.0, 250.0, power=1.8)\n"
;

const std::string simulate_docstring =
  "\n"
  "Simulates a Gaussian random field with the corresponding variogram in one, two or\n"
  "three dimensions. The random generator seed may be set by using gaussianfft.seed.\n"
  "\n"
  "Parameters\n"
  "----------\n"
  "variogram: gaussianfft.Variogram\n"
  "    An instance of gaussianfft.Variogram (see gaussianfft.variogram).\n"
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
  "out: numpy.ndarray\n"
  "    One-dimensional array with the simulation result. Uses Fortran ordering if the\n"
  "    simulation is multi-dimensional.\n"
  "\n"
  "Examples\n"
  "--------\n"
  ">>> v = gaussianfft.variogram('gaussian', 250.0, 125.0)\n"
  ">>> nx, dx = 10, 100.0\n"
  ">>> z = gaussianfft.simulate(v, nx, dx)\n"
  ">>> z\n"
  "array([-1.29924289, -1.51172913, -1.2935657 , -0.80779427,  0.22217236,\n"
  "        1.26740091,  0.66094991, -0.77396656,  0.01523847,  0.44392584])\n"
  "\n"
  "Multi-dimensional simulation\n"
  "\n"
  ">>> nx, ny = 100, 200\n"
  ">>> dx, dy = 10.0, 5.0\n"
  ">>> z = gaussianfft.simulate(v, nx, dx, ny, dy)\n"
  ">>> z_np = z.reshape((nx, ny), order='F')\n"
  ">>> z_np.shape\n"
  "(100,200)\n"
;

const std::string advanced_simulate_docstring =
  "\n"
  "Same as gaussianfft.simulate, but with a few additional advanced and\n"
  "experimental settings.\n"
  "\n"
  "Parameters\n"
  "----------\n"
  "variogram, nx, ny, nz, dx, dy, dz:\n"
  "    See gaussianfft.simulate.\n"
  "padx, pady, padz: int\n"
  "    Grid padding as a number of cells. In gaussianfft.simulate, these are set\n"
  "    automatically to the values returned by gaussianfft.simulation_size.\n"
  "sx, sy, sz: float\n"
  "    Gaussian smoothing parameters to reduce the range. The parameters are the\n"
  "    values of the smoothing kernel at one variogram range and MUST therefore be\n"
  "    greater than 0 and less than 1. A value close to or greater than 1 means no\n"
  "    smoothing.\n"
  "\n"
  "Returns\n"
  "-------\n"
  "out: numpy.ndarray\n"
  "    See gaussianfft.simulate.\n"
;

/**********************************************/
/**********************************************/
/**********************************************/

PYBIND11_MODULE(_gaussianfft, m)
{
  m.def("quote",&GaussFFT::Quote);

  //
  // Variogram class
  //
  {
    double(NRLib::Variogram::*ptr1)(double)                 const = &NRLib::Variogram::GetCorr;
    double(NRLib::Variogram::*ptr2)(double, double)         const = &NRLib::Variogram::GetCorr;
    double(NRLib::Variogram::*ptr3)(double, double, double) const = &NRLib::Variogram::GetCorr;
    py::class_<NRLib::Variogram>(m, "Variogram")
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
    m.def("seed", ptr,                          set_seed_docstring.c_str());
    m.def("seed", &NRLib::Random::GetStartSeed, get_seed_docstring.c_str());
  }

  //
  // Padding
  //
  m.def("simulation_size", &GaussFFT::FindGridSizeAfterPadding,
      py::arg("variogram"),
      py::arg("nx"),
      py::arg("dx"),
      py::arg("ny") = 1U,
      py::arg("dy") = -1.0,
      py::arg("nz") = 1U,
      py::arg("dz") = -1.0,
    padding_docstring.c_str()
  );

  //
  // Variogram factory function
  //
  m.def("variogram", &GaussFFT::CreateVariogram,
      py::arg("type"),
      py::arg("main_range"),
      py::arg("perp_range")=-1.0,
      py::arg("depth_range")=-1.0,
      py::arg("azimuth")=0.0,
      py::arg("dip")=0.0,
      // py::arg("sd")=1.0,
      py::arg("power")=1.5,
    py::return_value_policy::take_ownership,
    variogram_docstring.c_str()
  );

  // Simulate core function
  //
  m.def("simulate", &GaussFFT::Simulate,
      py::arg("variogram"),
      py::arg("nx"),
      py::arg("dx"),
      py::arg("ny")=1U,
      py::arg("dy")=-1.0,
      py::arg("nz")=1U,
      py::arg("dz")=-1.0,
    simulate_docstring.c_str()
  );

  /******************* Advanced *******************/
  auto advanced = m.def_submodule("advanced");
  //
  // Simulate core function
  //
  advanced.def("simulate", &GaussFFT::SimulateWithAdvancedSettings,
      py::arg("variogram"),
      py::arg("nx"),
      py::arg("dx"),
      py::arg("ny") = 1U,
      py::arg("dy") = -1.0,
      py::arg("nz") = 1U,
      py::arg("dz") = -1.0,
      py::arg("padx") = -1,
      py::arg("pady") = -1,
      py::arg("padz") = -1,
      py::arg("sx") = 1.0,
      py::arg("sy") = 1.0,
      py::arg("sz") = 1.0,
    advanced_simulate_docstring.c_str()
  );
}
