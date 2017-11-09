#define BOOST_PYTHON_STATIC_LIB

#include <boost/python.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>

// May want to reintroduce this later:
// #include <boost/python/numpy.hpp>

#include "gaussfft.hpp"

#include "nrlib/variogram/variogram.hpp"
#include "nrlib/random/random.hpp"

namespace bp = boost::python;

BOOST_PYTHON_MODULE(nrlib)
{
  bp::class_<std::vector<double> >("DoubleVector")
    .def(bp::vector_indexing_suite< std::vector<double> >())
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
    bp::return_value_policy<bp::manage_new_object>()
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
    )
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
