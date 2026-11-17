from __future__ import annotations

import numpy as np

import gaussianfft
from gaussianfft._kriging.covariance import Covariance
from gaussianfft._kriging.grid_spec import GridSpec


class Variogram(Covariance):
    """Stationary variogram, wrapping a ``gaussianfft.Variogram``."""

    def __init__(self, variogram: gaussianfft.Variogram):
        self._variogram = variogram

    @classmethod
    def from_parameters(
        cls, type, main_range: float, perp_range: float = -1.0, depth_range: float = -1.0, *,
        azimuth: float = 0.0, dip: float = 0.0, power: float = 1.5,
    ) -> Variogram:
        """Create from ``gaussianfft.variogram`` parameters."""
        return cls(gaussianfft.variogram(
            type, main_range=main_range, perp_range=perp_range, depth_range=depth_range,
            azimuth=azimuth, dip=dip, power=power,
        ))

    @property
    def variogram(self) -> gaussianfft.Variogram:
        """The wrapped ``gaussianfft.Variogram``."""
        return self._variogram

    def corr_matrix(self, points, locations) -> np.ndarray:
        points = np.asarray(points, dtype=float)
        corr = np.empty((len(points), len(locations)))
        for j, location in enumerate(np.asarray(locations, dtype=float)):
            corr[:, j] = self._variogram.corr_array(points - location)
        return corr

    def simulate(self, grid: GridSpec) -> np.ndarray:
        grid_args = tuple(value for axis in zip(grid.shape, grid.spacing) for value in axis)
        raw = gaussianfft.simulate(self._variogram, *grid_args)
        return np.asarray(raw).reshape(grid.shape, order='F')
