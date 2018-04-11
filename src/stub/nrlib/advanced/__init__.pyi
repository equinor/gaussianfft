from .. import Variogram
from typing import overload

from numpy import ndarray


@overload
def simulate(variogram: Variogram, nx: int, ny: int, nz: int, dx: float, dy: float, dz: float, padx: int, pady: int, padz: int, sx: float, sy: float, sz: float) -> ndarray:
    """
Same as nrlib.simulate, but with a few additional advanced and
experimental settings.

Parameters
----------
variogram: nrlib.Variogram
    An instance of nrlib.Variogram (see nrlib.variogram).
nx, ny, nz: int
    Grid size of the simulated field. Only nx is required. Setting ny and/or nz to
    a value less than or equal to 1 reduces the dimension. Default is ny = 1 and
    nz = 1.
dx, dy, dz: float
    Grid resolution in x, y and z directions. dx is always required. dy and dz are
    required if respectively ny and nz are greater than 1.
padx, pady, padz: int
    Grid padding as a number of cells. In nrlib.simulate, these are set
    automatically to the values returned by nrlib.simulation_size.
sx, sy, sz: float
    Gaussian smoothing parameters to reduce the range. The parameters are the
    values of the smoothing kernel at one variogram range and MUST therefore be
    greater than 0 and less than 1. A value close to or greater than 1 means no
    smoothing.

Returns
-------
out: numpy.ndarray
    See nrlib.simulate.
  """
    pass


@overload
def simulate(variogram: Variogram, nx: int, ny: int, dx: float, dy: float, padx: int, pady: int, sx: float, sy: float) -> ndarray:...


@overload
def simulate(variogram: Variogram, nx: int, dx: float, padx: int, sx: float) -> ndarray:...
