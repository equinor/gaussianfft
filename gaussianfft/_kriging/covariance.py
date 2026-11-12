from __future__ import annotations

import abc

import numpy as np

from gaussianfft._kriging.grid_spec import GridSpec


class Covariance(abc.ABC):
    """Gridless unit-variance covariance model, with correlation given by ``corr_matrix``."""

    @abc.abstractmethod
    def corr_matrix(self, points, locations) -> np.ndarray:
        """Correlation between points (n_points, ndim) and locations (n_locations, ndim)."""

    @abc.abstractmethod
    def simulate(self, grid: GridSpec) -> np.ndarray:
        """Unconditional unit-variance field with the grid shape."""
