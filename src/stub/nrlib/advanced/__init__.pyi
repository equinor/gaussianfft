from nrlib import Variogram
from typing import overload

from numpy import ndarray


@overload
def simulate(variogram: Variogram, nx: int, ny: int, nz: int, dx: float, dy: float, dz: float, padx: int, pady: int, padz: int, sx: float, sy: float, sz: float) -> ndarray: ...


@overload
def simulate(variogram: Variogram, nx: int, ny: int, dx: float, dy: float, padx: int, pady: int, sx: float, sy: float) -> ndarray: ...


@overload
def simulate(variogram: Variogram, nx: int, dx: float, padx: int, sx: float) -> ndarray: ...
