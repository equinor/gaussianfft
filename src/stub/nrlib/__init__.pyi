from nrlib import SizeTVector, Variogram
from typing import Optional, overload

from numpy import ndarray

"""
nrlib.variogram
"""


def variogram(type: str, main_range: float, perp_range: Optional[float], depth_range: Optional[float], azimuth: Optional[float], dip: Optional[float], power: Optional[float]) -> Variogram: ...


"""
nrlib.simulate
"""


@overload
def simulate(variogram: Variogram, nx: int, ny: int, nz: int, dx: float, dy: float, dz: float) -> ndarray: ...


@overload
def simulate(variogram: Variogram, nx: int, ny: int, dx: float, dy: float) -> ndarray: ...


@overload
def simulate(variogram: Variogram, nx: int, nz: int, dx: float, dz: float) -> ndarray: ...


@overload
def simulate(variogram: Variogram, nx: int, dx: float) -> ndarray: ...


"""
nrlib.seed
"""


@overload
def seed(arg1: int) -> None: ...


@overload
def seed() -> int: ...


"""
nrlib.simulation_size
"""


@overload
def simulation_size(variogram: Variogram, nx: int, dx: float, ny: int, dy: float, nz: int,dz: float) -> SizeTVector: ...


@overload
def simulation_size(variogram: Variogram, nx: int, dx: float, ny: int, dy: float) -> SizeTVector: ...


@overload
def simulation_size(variogram: Variogram, nx: int, dx: float) -> SizeTVector: ...
