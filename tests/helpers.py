import numpy as np
import numpy.typing as npt
import math
from typing import Union


# This is a pure Python implementation of the chi2 probability distribution
# which we use in one of the tests.
# The main reason for this is that pypy requires scipy to be compiled from source
# which is quite cumbersome and time-consuming to do in the CI.


class chi2:
    @staticmethod
    def pdf(x: Union[npt.NDArray, float], df: int) -> npt.NDArray:
        """Probability density function at x of the given RV.

        :param x: quantiles
        :param df: degrees of freedom
        :returns: Probability density function evaluated at x"""
        return 1 / (2 ** (df / 2) * math.gamma(df / 2) ) * x ** (df / 2 - 1) * np.exp(-x / 2)

    @classmethod
    def ppf(cls, q: float, df: int):
        """Percent point function (inverse of cdf) at q of the given RV.

        :param q: lower tail probability
        :param df: degrees of freedom
        :returns: quantile corresponding to the lower tail probability q."""
        prob_range = 1500  # The pdf at this point is 0.0
        prob_resolution = 0.001
        _x = np.linspace(0, prob_range, int(1 / prob_resolution) * prob_range + 1)
        probabilities = cls.pdf(_x, df)
        cdf = probabilities.cumsum()
        cdf /= max(cdf)
        return _x[cdf <= q][-1]
