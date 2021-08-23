from .. import Variogram
from typing import overload

from numpy import ndarray


@overload
def simulate(
        variogram: Variogram,
        nx: int, dx: float,
        ny: int = 1, dy: float = -1.0,
        nz: int = 1, dz: float = -1.0,

        padx: int = -1, pady: int = -1, padz: int = -1,

        sx: float = 1.0, sy: float = 1.0, sz: float = 1.0,
) -> ndarray:
    """
Same as gaussianfft.simulate, but with a few additional advanced and
experimental settings.

Parameters
----------
variogram: gaussianfft.Variogram
    An instance of gaussianfft.Variogram (see gaussianfft.variogram).
nx, ny, nz: int
    Grid size of the simulated field. Only nx is required. Setting ny and/or nz to
    a value less than or equal to 1 reduces the dimension. Default is ny = 1 and
    nz = 1.
dx, dy, dz: float
    Grid resolution in x, y and z directions. dx is always required. dy and dz are
    required if respectively ny and nz are greater than 1.
padx, pady, padz: int
    Grid padding as a number of cells. In gaussianfft.simulate, these are set
    automatically to the values returned by gaussianfft.simulation_size.
sx, sy, sz: float
    Gaussian smoothing parameters to reduce the range. The parameters are the
    values of the smoothing kernel at one variogram range and MUST therefore be
    greater than 0 and less than 1. A value close to or greater than 1 means no
    smoothing.

Returns
-------
out: numpy.ndarray
    See gaussianfft.simulate.
  """
    pass


@overload
def simulate(
        variogram: Variogram,
        nx: int, dx: float,
        ny: int = 1, dy: float = -1.0,
        padx: int = -1, pady: int = -1,
        sx: float = 1.0, sy: float = 1.0,
) -> ndarray:...


@overload
def simulate(
        variogram: Variogram,
        nx: int,
        dx: float,
        padx: int = -1,
        sx: float = 1.0,
) -> ndarray:...
