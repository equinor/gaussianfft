from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class GridSpec:
    """Regular grid with axes in x, y, z order and an optional world-space origin."""

    shape: tuple[int, ...]
    spacing: tuple[float, ...]
    origin: np.ndarray | None = None

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
        if not np.all(np.isfinite(self.spacing)) or np.any(np.asarray(self.spacing) <= 0):
            raise ValueError("grid_spacing must contain positive finite values")
        self.origin = (
            np.zeros(len(self.shape)) if self.origin is None
            else np.array(self.origin, dtype=float, copy=True)
        )
        if self.origin.shape != (len(self.shape),) or not np.all(np.isfinite(self.origin)):
            raise ValueError("origin must contain one finite value per grid dimension")

    def coordinates(self) -> np.ndarray:
        """Return node coordinates in the same C-order as grid-shaped outputs."""
        axes = [
            origin + np.arange(size) * spacing
            for size, spacing, origin in zip(self.shape, self.spacing, self.origin)
        ]
        return np.stack(np.meshgrid(*axes, indexing='ij'), axis=-1).reshape(-1, len(self.shape))
