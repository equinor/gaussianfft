from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class GridSpec:
    """Regular grid with cell counts in x, y, z order and lower faces at zero."""

    shape: tuple[int, ...]
    spacing: tuple[float, ...]

    def __post_init__(self):
        self.shape = tuple(self.shape)
        self.spacing = tuple(self.spacing)
        if not 1 <= len(self.shape) <= 3:
            raise ValueError("grid_shape must contain 1, 2, or 3 dimensions")
        if len(self.spacing) != len(self.shape):
            raise ValueError("grid_spacing must have the same length as grid_shape")
        if any(
            not isinstance(size, (int, np.integer))
            or isinstance(size, (bool, np.bool_)) or size <= 0
            for size in self.shape
        ):
            raise ValueError("grid_shape must contain positive integers")
        if len(self.shape) == 3 and self.shape[1] == 1 and self.shape[2] > 1:
            raise ValueError("Kriging does not currently support x-z slices (ny == 1 and nz > 1)")
        if not np.all(np.isfinite(self.spacing)) or np.any(np.asarray(self.spacing) <= 0):
            raise ValueError("grid_spacing must contain positive finite values")

    def coordinates(self) -> np.ndarray:
        """Return cell centers in the same C-order as grid-shaped outputs."""
        axes = [
            (np.arange(size) + 0.5) * spacing
            for size, spacing in zip(self.shape, self.spacing)
        ]
        return np.stack(np.meshgrid(*axes, indexing='ij'), axis=-1).reshape(-1, len(self.shape))
