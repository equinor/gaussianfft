from __future__ import annotations

import abc

import numpy as np
try:
    import scipy.linalg
    import scipy.ndimage
except ImportError:
    raise ImportError("Scipy is not installed, and is required to use these utilities")

from gaussianfft._kriging.covariance import Covariance
from gaussianfft._kriging.grid_spec import GridSpec
from gaussianfft._kriging.observation_data import ObservationData


class FactorizationError(ValueError):
    def __init__(self):
        super().__init__(
            "Failed to factorize observation covariance matrix. "
            "The matrix is likely not positive definite. This can happen for "
            "nearly duplicate observation locations with too small observation "
            "uncertainties. Consider increasing obs_uncertainties or removing "
            "duplicate/near-duplicate observations."
        )

# Each cross-covariance chunk holds (chunk_size × n_obs) float64 values.
# Chunking keeps peak memory bounded while BLAS still operates on full batches.
_MEMORY_BUDGET_BYTES = 10 * 1024 * 1024 * 1024  # 10 GB


# ---------------------------------------------------------------------------
# Module-level utilities
# ---------------------------------------------------------------------------

def _build_obs_cov_matrix(variogram: Covariance, obs_locations, obs_uncertainties):
    cov = variogram.corr_matrix(obs_locations, obs_locations)
    cov[np.diag_indices(len(obs_locations))] += obs_uncertainties ** 2 + 1e-10
    return cov


def _cholesky_factor(cov):
    """Factorize an observation covariance matrix, reporting non-positive definiteness."""
    try:
        return scipy.linalg.cho_factor(cov)
    except scipy.linalg.LinAlgError as exc:
        raise FactorizationError() from exc


def _chunk_size(n_grid, n_obs):
    """Grid points per batch so peak working memory stays within _MEMORY_BUDGET_BYTES.

    Each chunk iteration allocates ~4 arrays of shape (chunk, n_obs):
    K, beta, weights, and temporaries.  We divide the budget by 4 to account
    for this.  When the whole grid fits in one chunk (the common 2D case)
    the loop body executes exactly once, identical to the old fully-vectorised path.
    """
    arrays_per_chunk = 4
    return min(n_grid, max(1, _MEMORY_BUDGET_BYTES // (arrays_per_chunk * n_obs * 8)))


def _obs_interp_coords(obs_locations, grid: GridSpec):
    relative_locations = obs_locations - grid.origin
    grid_max = (np.asarray(grid.shape) - 1) * grid.spacing
    if np.any(relative_locations < 0) or np.any(relative_locations > grid_max):
        raise ValueError("obs_locations has values outside grid bounds for simulation")
    return (relative_locations / grid.spacing).T


def _interpolate_at_obs(field, obs_coords):
    return scipy.ndimage.map_coordinates(field, obs_coords, order=1)


# ---------------------------------------------------------------------------
# Kriging classes
# ---------------------------------------------------------------------------


class Kriging(abc.ABC):
    """Kriging interface accepting observations and a variogram per operation."""

    @abc.abstractmethod
    def predict(
        self, grid: GridSpec, obs: ObservationData, variogram: Covariance,
        calculate_stddev=False,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        """Return a grid-shaped prediction and optional standard deviation."""

    @abc.abstractmethod
    def simulate(
        self, grid: GridSpec, obs: ObservationData, variogram: Covariance,
        n_sim=1,
    ) -> list[np.ndarray]:
        """Generate conditional fields on a grid covering all observation locations."""


class SimpleKriging(Kriging):
    """Simple kriging with a known constant scalar mean."""

    def __init__(self, mean: float = 0.0):
        self.mean = float(mean)
        self._obs = None
        self._variogram = None
        self._cho_factor = None

    def _initialize(self, obs: ObservationData, variogram: Covariance) -> None:
        covariance = _build_obs_cov_matrix(variogram, obs.locations, obs.uncertainties)
        cho_factor = _cholesky_factor(covariance)
        self._obs = obs
        self._variogram = variogram
        self._cho_factor = cho_factor

    def predict(
        self, grid: GridSpec, obs: ObservationData, variogram: Covariance,
        calculate_stddev=False,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        if obs.locations.shape[1] != len(grid.shape):
            raise ValueError(f"obs_locations must have {len(grid.shape)} columns for this grid")
        self._initialize(obs, variogram)
        grid_coords = grid.coordinates()
        residuals = obs.values - self.mean
        correction, stddev = self._krige(grid.shape, grid_coords, residuals, calculate_stddev)
        correction += self.mean
        return correction, stddev

    def simulate(
        self, grid: GridSpec, obs: ObservationData, variogram: Covariance,
        n_sim=1,
    ) -> list[np.ndarray]:
        if obs.locations.shape[1] != len(grid.shape):
            raise ValueError(f"obs_locations must have {len(grid.shape)} columns for this grid")
        self._initialize(obs, variogram)
        grid_coords = grid.coordinates()
        obs_coords = _obs_interp_coords(obs.locations, grid)
        results = []

        for _ in range(n_sim):
            uncond = self._variogram.simulate(grid)
            uncond_at_obs = _interpolate_at_obs(uncond, obs_coords)
            obs_residuals = (obs.values - self.mean) - uncond_at_obs

            correction, _ = self._krige(grid.shape, grid_coords, obs_residuals)
            results.append(self.mean + uncond + correction)
        return results

    def _krige(self, grid_shape: tuple[int, ...], grid_coords, residuals, calculate_stddev=False):
        """Apply simple kriging to mean-adjusted observation or simulation residuals."""
        obs = self._obs
        weights = scipy.linalg.cho_solve(self._cho_factor, residuals)
        n_grid = len(grid_coords)
        n_obs = len(obs.locations)
        chunk = _chunk_size(n_grid, n_obs)
        correction_flat = np.empty(n_grid)
        variance_flat = np.empty(n_grid) if calculate_stddev else None
        for start in range(0, n_grid, chunk):
            end = min(start + chunk, n_grid)
            cross_cov = self._variogram.corr_matrix(grid_coords[start:end], obs.locations)
            correction_flat[start:end] = cross_cov @ weights
            if calculate_stddev:
                alpha = scipy.linalg.cho_solve(self._cho_factor, cross_cov.T)
                variance_flat[start:end] = 1.0 - np.sum(cross_cov * alpha.T, axis=1)

        correction = correction_flat.reshape(grid_shape)
        stddev = None
        if calculate_stddev:
            stddev = np.sqrt(np.maximum(variance_flat, 0.0)).reshape(grid_shape)
        return correction, stddev


class OrdinaryKriging(Kriging):
    """Ordinary kriging with an unknown constant mean estimated per operation.

    The unbiasedness constraint (weights sum to 1) is enforced via a Lagrange
    multiplier.  Weights and drift coefficient are computed on-the-fly in
    chunks via the Schur complement of C, using only the Cholesky factor of C.
    Beyond the covariance factor, only O(n_obs) scalars are stored after initialization::

        alpha  = C^{-1} 1                          (n_obs,)  stored
        s      = 1^T alpha                          scalar    stored
        -- per chunk (chunk_size grid points at a time) --
        beta   = C^{-1} K^T                         (n_obs, cs)
        mu(x)  = (alpha^T K^T - 1) / s             (cs,)  [drift coefficient]
        w(x)   = beta - alpha * mu(x)               (n_obs, cs)

    Kriging mean:     z*(x) = w(x)^T z_obs
    Kriging variance: sigma^2(x) = C(0) - k(x)^T w(x) - mu(x)
    """

    def __init__(self):
        self._obs = None
        self._variogram = None
        self._cho_factor = None
        self._alpha = np.empty(0)
        self._s = 0.0
        self.estimated_mean = None

    def _initialize(self, obs: ObservationData, variogram: Covariance) -> None:
        covariance = _build_obs_cov_matrix(variogram, obs.locations, obs.uncertainties)
        cho_factor = _cholesky_factor(covariance)
        n_obs = len(obs.locations)
        ones = np.ones(n_obs)
        alpha = scipy.linalg.cho_solve(cho_factor, ones)
        normalization = float(alpha.sum())
        gamma = scipy.linalg.cho_solve(cho_factor, obs.values)
        estimated_mean = float(gamma.sum() / normalization)
        self._obs = obs
        self._variogram = variogram
        self._cho_factor = cho_factor
        self._alpha = alpha
        self._s = normalization
        self.estimated_mean = estimated_mean

    def _ok_weights_chunk(self, cross_cov):
        """Return ordinary-kriging weights and drift for a cross-covariance chunk."""
        beta = scipy.linalg.cho_solve(self._cho_factor, cross_cov.T)
        drift = (self._alpha @ cross_cov.T - 1.0) / self._s
        return beta - np.outer(self._alpha, drift), drift

    def predict(
        self, grid: GridSpec, obs: ObservationData, variogram: Covariance,
        calculate_stddev=False,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        if obs.locations.shape[1] != len(grid.shape):
            raise ValueError(f"obs_locations must have {len(grid.shape)} columns for this grid")
        self._initialize(obs, variogram)
        grid_coords = grid.coordinates()
        return self._krige(grid.shape, grid_coords, obs.values, calculate_stddev)

    def simulate(
        self, grid: GridSpec, obs: ObservationData, variogram: Covariance,
        n_sim=1,
    ) -> list[np.ndarray]:
        if obs.locations.shape[1] != len(grid.shape):
            raise ValueError(f"obs_locations must have {len(grid.shape)} columns for this grid")
        self._initialize(obs, variogram)
        grid_coords = grid.coordinates()
        obs_coords = _obs_interp_coords(obs.locations, grid)
        results = []

        for _ in range(n_sim):
            uncond = self._variogram.simulate(grid)
            uncond_at_obs = _interpolate_at_obs(uncond, obs_coords)
            obs_residuals = obs.values - uncond_at_obs

            correction, _ = self._krige(grid.shape, grid_coords, obs_residuals)
            results.append(uncond + correction)
        return results

    def _krige(self, grid_shape: tuple[int, ...], grid_coords, residuals, calculate_stddev=False):
        """Apply ordinary kriging to observation values or simulation residuals."""
        obs = self._obs
        n_grid = len(grid_coords)
        n_obs = len(obs.locations)
        chunk = _chunk_size(n_grid, n_obs)
        correction_flat = np.empty(n_grid)
        variance_flat = np.empty(n_grid) if calculate_stddev else None
        for start in range(0, n_grid, chunk):
            end = min(start + chunk, n_grid)
            cross_cov = self._variogram.corr_matrix(grid_coords[start:end], obs.locations)
            weights, drift = self._ok_weights_chunk(cross_cov)
            correction_flat[start:end] = weights.T @ residuals
            if calculate_stddev:
                variance_flat[start:end] = 1.0 - np.sum(cross_cov * weights.T, axis=1) - drift

        correction = correction_flat.reshape(grid_shape)
        stddev = None
        if calculate_stddev:
            stddev = np.sqrt(np.maximum(variance_flat, 0.0)).reshape(grid_shape)
        return correction, stddev
