// $Id: delta.hpp 1468 2017-04-21 13:09:33Z perroe $

// Copyright (c)  2012, Norwegian Computing Center
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

#ifndef NRLIB_RANDOM_DELTA_HPP
#define NRLIB_RANDOM_DELTA_HPP

#include "distribution.hpp"

#include <cassert>
#include <limits>

namespace NRLib {

class Delta : public Distribution<double> {
public:
  Delta();
  explicit Delta(double val);
  ~Delta();

  Distribution<double>* Clone() const;

  inline void SetParameters(double val);

  // The Delta distribution should be used with care.
  // The Pdf-function returns 0 or infinity.
  inline double Pdf(double x) const;
  inline double Cdf(double x) const;
  inline double Quantile(double x) const;

private:
  double val_;
};


// ---------------- IMPLEMENTATION OF INLINE FUNCTIONS -----------------

void Delta::SetParameters(double val) {
  val_ = val;
}


double Delta::Pdf(double x) const {
  double p = 0.0;
  if (x == val_)
    p = std::numeric_limits<double>::infinity();
  return p;
}


double Delta::Cdf(double x) const {
  double p = 0.0;
  if (x >= val_) {
    p = 1.0;
  }
  return p;
}


double Delta::Quantile(double /*p*/) const {
  return val_;
}

} // namespace NRLib

#endif // NRLIB_RANDOM_DELTA_HPP
