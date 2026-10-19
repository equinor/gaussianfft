from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ObservationData:
    """Observation coordinates, values, and error standard deviations in field units."""

    locations: np.ndarray
    values: np.ndarray
    uncertainties: np.ndarray

    def __post_init__(self):
        self.locations = np.array(self.locations, dtype=float, copy=True)
        self.values = np.array(self.values, dtype=float, copy=True)
        self.uncertainties = np.array(self.uncertainties, dtype=float, copy=True)
        if self.locations.ndim != 2:
            raise ValueError("obs_locations must be a 2D array")
        if not 1 <= self.locations.shape[1] <= 3:
            raise ValueError("obs_locations must have 1, 2, or 3 columns")
        count = len(self.locations)
        if count == 0:
            raise ValueError("at least one observation is required")
        if self.values.shape != (count,):
            raise ValueError(f"obs_values must have shape ({count},), got {self.values.shape}")
        if self.uncertainties.shape != (count,):
            raise ValueError(
                f"obs_uncertainties must have shape ({count},), got {self.uncertainties.shape}"
            )
        if not all(np.all(np.isfinite(array)) for array in (
            self.locations, self.values, self.uncertainties,
        )):
            raise ValueError("observations must contain only finite values")
        if np.any(self.uncertainties < 0):
            raise ValueError("obs_uncertainties must be non-negative")
