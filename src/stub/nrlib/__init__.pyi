from typing import Collection, Iterable, Optional, Union, overload

from numpy import ndarray

Number = Union[int, float]


class DoubleVector(object, Collection):
    def append(self, num: Number) -> None: ...

    def extend(self, iterable: Iterable[Number]) -> None: ...


class SizeTVector(object, Collection):
    def append(self, num: Number) -> None: ...

    def extend(self, iterable: Iterable[Number]) -> None: ...


class Variogram(object):
    @overload
    def corr(self, dx: float, dy: float, dz: float) -> float:...

    @overload
    def corr(self, dx: float, dy: float) -> float:...

    @overload
    def corr(self, dx: float) -> float:...


"""
nrlib.variogram
"""


def variogram(type: str, main_range: float, perp_range: Optional[float], depth_range: Optional[float], azimuth: Optional[float], dip: Optional[float], power: Optional[float]) -> Variogram:
    """Factory function for creating a particular variogram. The variogram is always
defined in three directions, but for simulation in fewer dimensions than three,
only the corresponding number of directions are used.

Parameters
----------
type: string
    A string representing the type of variogram. The following types are supported:
    gaussian, exponential, general_exponential, spherical, matern32, matern52,
    matern72 and constant.
main_range: float
    Range of the variogram in the main direction.
perp_range, depth_range: floats, optional
    Parameters representing the range of the variogram in the two directions
    perpendicular to main_range. If any of these are zero, the default is to set
    the value to the same as main_range.
azimuth: float, optional
    Lateral orientation of the variogram in degrees. Default is 0.0.
dip: float, optional
    Dip direction of the variogram in degrees. Default is 0.0
power: float, optional
    Power of the exponent for the general_exponential variogram, which is the only
    variogram type this is used for. Default is 1.5.

Returns
-------
out: Variogram
    An instance of the class nrlib.Variogram.

Examples
--------
>>> import nrlib
>>> nrlib.variogram('gaussian', 1000.0)

Specifying dip

>>> nrlib.variogram('matern52', 1000.0, dip=45.0)

Multiple directions

>>> nrlib.variogram('general_exponential', 1000.0, 500.0, 250.0, power=1.8)
"""
    pass


"""
nrlib.simulate
"""


@overload
def simulate(variogram: Variogram, nx: int, ny: int, nz: int, dx: float, dy: float, dz: float) -> ndarray:
    """
Simulates a Gaussian random field with the corresponding variogram in one, two or
three dimensions. The random generator seed may be set by using nrlib.seed.

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

Returns
-------
out: numpy.ndarray
    One-dimensional array with the simulation result. Uses Fortran ordering if the
    simulation is multi-dimensional.

Examples
--------
>>> import nrlib
>>> v = nrlib.variogram('gaussian', 250.0, 125.0)
>>> nx, dx = 10, 100.0
>>> z = nrlib.simulate(v, nx, dx)
>>> z
>>>array([-1.29924289, -1.51172913, -1.2935657 , -0.80779427,  0.22217236,
>>>        1.26740091,  0.66094991, -0.77396656,  0.01523847,  0.44392584])

Multi-dimensional simulation

>>> nx, ny = 100, 200
>>> dx, dy = 10.0, 5.0
>>> z = nrlib.simulate(v, nx, dx, ny, dy)
>>> z_np = z.reshape((nx, ny), order='F')
>>> z_np.shape
>>>(100,200)
"""
    pass


@overload
def simulate(variogram: Variogram, nx: int, ny: int, dx: float, dy: float) -> ndarray:...


@overload
def simulate(variogram: Variogram, nx: int, nz: int, dx: float, dz: float) -> ndarray:...


@overload
def simulate(variogram: Variogram, nx: int, dx: float) -> ndarray:...


"""
nrlib.seed
"""


@overload
def seed(seed: int) -> None:
    """
Sets the current simulation seed. If this has not been set when calling
nrlib.simulate, it is set to the current time with second precision. Be wary of
the latter, in particular if nrlib is used in a parallel-processing context.

Examples
--------
>>> import nrlib
>>> nrlib.seed(123)
    """
    pass


@overload
def seed() -> int:
    """
Gets the current simulation seed. Throws RunTimeError if the seed has not been set
yet.

Examples
--------
>>> import nrlib
>>> nrlib.seed(123)
>>> nrlib.seed()
>>>12
    """
    pass


"""
nrlib.simulation_size
"""


@overload
def simulation_size(variogram: Variogram, nx: int, dx: float, ny: int, dy: float, nz: int, dz: float) -> SizeTVector: ...


@overload
def simulation_size(variogram: Variogram, nx: int, dx: float, ny: int, dy: float) -> SizeTVector: ...


@overload
def simulation_size(variogram: Variogram, nx: int, dx: float) -> SizeTVector: ...
