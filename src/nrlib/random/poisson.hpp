// $Id: poisson.hpp 1468 2017-04-21 13:09:33Z perroe $

// Copyright (c)  2011, Norwegian Computing Center
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

#ifndef NRLIB_RANDOM_POISSON_HPP
#define NRLIB_RANDOM_POISSON_HPP

#include "distribution.hpp"
#include "../exception/exception.hpp"

#include <cmath>
#include <vector>

namespace NRLib {

class Poisson : public Distribution<int>
{
public:
  explicit Poisson(double lambda);
  ~Poisson();

  Distribution<int>* Clone() const;

  double Pdf(int x) const ;
  double Cdf(int x) const ;
  int Quantile(double q) const ;
  int Draw() const;
  int Draw(RandomGenerator & g) const;

private:
  double lambda_;
  double exp_mean_;
  double smu_;
  double a_;
  double b_;
  double inv_alpha_;
  double v_r_;

};

} //namespace NRLib
#endif
