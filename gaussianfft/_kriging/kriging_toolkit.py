import numpy as np
import scipy.linalg
import scipy.ndimage

import gaussianfft

_FACTORIZE_ERROR = (
    "Failed to factorize observation covariance matrix. "
    "The matrix is likely not positive definite. This can happen for "
    "nearly duplicate observation locations with too small observation "
    "uncertainties. Consider increasing obs_uncertainties or removing "
    "duplicate/near-duplicate observations."
)

# Each cross-covariance chunk holds (chunk_size × n_obs) float64 values.
# Chunking keeps peak memory bounded while BLAS still operates on full batches.
_MEMORY_BUDGET_BYTES = 1 * 1024 * 1024 * 1024  # 1 GB


# ---------------------------------------------------------------------------
# Module-level utilities
# ---------------------------------------------------------------------------

def _ndims(ny, nz):
    return 3 if nz > 1 else (2 if ny > 1 else 1)


def _validate_inputs(obs_locations, obs_values, obs_uncertainties,
                     nx, dx, ny, dy, nz, dz, ndims):
    if obs_locations.ndim != 2:
        raise ValueError(
            f"obs_locations must be a 2D array with shape (N, {ndims}), got {obs_locations.shape}"
        )
    if obs_locations.shape[1] != ndims:
        raise ValueError(
            f"obs_locations must have {ndims} columns, got {obs_locations.shape[1]}"
        )
    n = obs_locations.shape[0]
    if obs_values.shape != (n,):
        raise ValueError(f"obs_values must have shape ({n},), got {obs_values.shape}")
    if obs_uncertainties.shape != (n,):
        raise ValueError(f"obs_uncertainties must have shape ({n},), got {obs_uncertainties.shape}")
    if np.any(obs_uncertainties < 0):
        raise ValueError("obs_uncertainties must be non-negative")
    sizes = np.array((nx, ny, nz)[:ndims])
    steps = np.array((dx, dy, dz)[:ndims])
    grid_max = (sizes - 1) * steps
    if np.any(obs_locations < 0) or np.any(obs_locations > grid_max):
        raise ValueError("obs_locations has values outside grid bounds")


def _corr(variogram, dist, ndims):
    if ndims == 1:
        return variogram.corr(dist[0])
    elif ndims == 2:
        return variogram.corr(dist[0], dist[1])
    else:
        return variogram.corr(dist[0], dist[1], dist[2])


def _grid_coordinates(nx, dx, ny, dy, nz, dz, ndims):
    x = np.arange(nx) * dx
    if ndims == 1:
        return x.reshape(-1, 1)
    y = np.arange(ny) * dy
    if ndims == 2:
        xx, yy = np.meshgrid(x, y, indexing='ij')
        return np.column_stack([xx.ravel(), yy.ravel()])
    z = np.arange(nz) * dz
    xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')
    return np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])


def _build_obs_cov_matrix(variogram, obs_locations, obs_uncertainties, ndims):
    n = len(obs_locations)
    cov = np.empty((n, n))
    for i in range(n):
        for j in range(i, n):
            c = _corr(variogram, obs_locations[i] - obs_locations[j], ndims)
            cov[i, j] = c
            cov[j, i] = c
    cov[np.diag_indices(n)] += obs_uncertainties ** 2 + 1e-10
    return cov


def _chunk_size(n_grid, n_obs):
    """Grid points per batch so peak working memory stays within _MEMORY_BUDGET_BYTES.

    Each chunk iteration allocates ~4 arrays of shape (chunk, n_obs):
    K, beta, weights, and temporaries.  We divide the budget by 4 to account
    for this.  When the whole grid fits in one chunk (the common 2D case)
    the loop body executes exactly once, identical to the old fully-vectorised path.
    """
    arrays_per_chunk = 4
    return min(n_grid, max(1, _MEMORY_BUDGET_BYTES // (arrays_per_chunk * n_obs * 8)))


def _build_cov_chunk(variogram, grid_coords, start, end, obs_locations, ndims):
    """Cross-covariance K[start:end, :] between a chunk of grid points and all obs."""
    chunk = grid_coords[start:end]   # (chunk_size, ndims)
    n_obs = len(obs_locations)
    cov = np.empty((end - start, n_obs))
    for j in range(n_obs):
        dists = chunk - obs_locations[j]
        for i in range(end - start):
            cov[i, j] = _corr(variogram, dists[i], ndims)
    return cov


def _obs_interp_coords(obs_locations, dx, dy, dz, ndims):
    steps = np.array((dx, dy, dz)[:ndims])
    return (obs_locations / steps).T


def _interpolate_at_obs(field, obs_coords):
    return scipy.ndimage.map_coordinates(field, obs_coords, order=1)


def _simulate_uncond(variogram, nx, dx, ny, dy, nz, dz, grid_shape, ndims):
    if ndims == 1:
        raw = gaussianfft.simulate(variogram, nx, dx)
    elif ndims == 2:
        raw = gaussianfft.simulate(variogram, nx, dx, ny, dy)
    else:
        raw = gaussianfft.simulate(variogram, nx, dx, ny, dy, nz, dz)
    return np.array(raw).reshape(grid_shape, order='F')


# ---------------------------------------------------------------------------
# Kriging classes
# ---------------------------------------------------------------------------

class SimpleKriging:
    def __init__(self, variogram, nx, dx, ny, dy, nz, dz,
                 obs_locations, obs_values, obs_uncertainties, *, mean=0.0):
        self.variogram = variogram
        self.nx, self.dx = nx, dx
        self.ny, self.dy = ny, dy
        self.nz, self.dz = nz, dz
        self.mean = mean

        self.obs_locations = np.asarray(obs_locations, dtype=float)
        self.obs_values = np.asarray(obs_values, dtype=float)
        self.obs_uncertainties = np.asarray(obs_uncertainties, dtype=float)

        self.ndims = _ndims(ny, nz)
        self._grid_shape = (nx, ny, nz)[:self.ndims]
        if isinstance(self.mean, np.ndarray) and self.mean.shape != self._grid_shape:
            raise ValueError(
                f"mean must be a scalar or have shape {self._grid_shape}, got {self.mean.shape}"
            )

        _validate_inputs(self.obs_locations, self.obs_values, self.obs_uncertainties,
                         nx, dx, ny, dy, nz, dz, self.ndims)

        cov = _build_obs_cov_matrix(variogram, self.obs_locations, self.obs_uncertainties, self.ndims)
        try:
            self._cho_factor = scipy.linalg.cho_factor(cov)
        except scipy.linalg.LinAlgError as exc:
            raise ValueError(_FACTORIZE_ERROR) from exc

        self._grid_coords = _grid_coordinates(nx, dx, ny, dy, nz, dz, self.ndims)
        self._obs_coords = _obs_interp_coords(self.obs_locations, dx, dy, dz, self.ndims)

    def _mean_components(self):
        if isinstance(self.mean, np.ndarray):
            return _interpolate_at_obs(self.mean, self._obs_coords), self.mean
        return self.mean, self.mean

    def predict(self):
        mean_at_obs, mean_field = self._mean_components()
        residuals = self.obs_values - mean_at_obs
        sk_weights = scipy.linalg.cho_solve(self._cho_factor, residuals)   # (n_obs,)

        n_grid = self._grid_coords.shape[0]
        n_obs = len(self.obs_locations)
        chunk = _chunk_size(n_grid, n_obs)
        mean_flat = None if np.isscalar(mean_field) else mean_field.ravel()
        kriging_mean_flat = np.empty(n_grid)
        kriging_var_flat = np.empty(n_grid)

        for start in range(0, n_grid, chunk):
            end = min(start + chunk, n_grid)
            K = _build_cov_chunk(self.variogram, self._grid_coords, start, end,
                                 self.obs_locations, self.ndims)           # (cs, n_obs)
            alpha = scipy.linalg.cho_solve(self._cho_factor, K.T)         # (n_obs, cs)
            m = mean_field if mean_flat is None else mean_flat[start:end]
            kriging_mean_flat[start:end] = m + K @ sk_weights
            kriging_var_flat[start:end] = 1.0 - np.sum(K * alpha.T, axis=1)

        kriging_mean = kriging_mean_flat.reshape(self._grid_shape)
        kriging_stdev = np.sqrt(np.maximum(kriging_var_flat, 0.0)).reshape(self._grid_shape)
        return kriging_mean, kriging_stdev

    def simulate(self, n_sim=1):
        n_grid = self._grid_coords.shape[0]
        n_obs = len(self.obs_locations)
        chunk = _chunk_size(n_grid, n_obs)
        results = []

        for _ in range(n_sim):
            mean_at_obs, mean_field = self._mean_components()
            uncond = _simulate_uncond(
                self.variogram, self.nx, self.dx, self.ny, self.dy,
                self.nz, self.dz, self._grid_shape, self.ndims
            )
            uncond_at_obs = _interpolate_at_obs(uncond, self._obs_coords)
            obs_residuals = (self.obs_values - mean_at_obs) - uncond_at_obs
            sim_weights = scipy.linalg.cho_solve(self._cho_factor, obs_residuals)  # (n_obs,)

            correction_flat = np.empty(n_grid)
            for start in range(0, n_grid, chunk):
                end = min(start + chunk, n_grid)
                K = _build_cov_chunk(self.variogram, self._grid_coords, start, end,
                                     self.obs_locations, self.ndims)
                correction_flat[start:end] = K @ sim_weights

            results.append(mean_field + uncond + correction_flat.reshape(self._grid_shape))
        return results


class OrdinaryKriging:
    """Ordinary Kriging: estimates an unknown constant mean from the data.

    The unbiasedness constraint (weights sum to 1) is enforced via a Lagrange
    multiplier.  Weights and drift coefficient are computed on-the-fly in
    chunks via the Schur complement of C, using only the Cholesky factor of C.
    Only O(n_obs) scalars are stored after construction::

        alpha  = C^{-1} 1                          (n_obs,)  stored
        s      = 1^T alpha                          scalar    stored
        -- per chunk (chunk_size grid points at a time) --
        beta   = C^{-1} K^T                         (n_obs, cs)
        mu(x)  = (alpha^T K^T - 1) / s             (cs,)  [drift coefficient]
        w(x)   = beta - alpha * mu(x)               (n_obs, cs)

    Kriging mean:     z*(x) = w(x)^T z_obs
    Kriging variance: sigma^2(x) = C(0) - k(x)^T w(x) - mu(x)
    """

    def __init__(self, variogram, nx, dx, ny, dy, nz, dz,
                 obs_locations, obs_values, obs_uncertainties):
        self.variogram = variogram
        self.nx, self.dx = nx, dx
        self.ny, self.dy = ny, dy
        self.nz, self.dz = nz, dz

        self.obs_locations = np.asarray(obs_locations, dtype=float)
        self.obs_values = np.asarray(obs_values, dtype=float)
        self.obs_uncertainties = np.asarray(obs_uncertainties, dtype=float)

        self.ndims = _ndims(ny, nz)
        self._grid_shape = (nx, ny, nz)[:self.ndims]
        n_obs = len(self.obs_locations)

        _validate_inputs(self.obs_locations, self.obs_values, self.obs_uncertainties,
                         nx, dx, ny, dy, nz, dz, self.ndims)

        cov = _build_obs_cov_matrix(variogram, self.obs_locations, self.obs_uncertainties, self.ndims)
        try:
            self._cho_factor = scipy.linalg.cho_factor(cov)
        except scipy.linalg.LinAlgError as exc:
            raise ValueError(_FACTORIZE_ERROR) from exc

        self._grid_coords = _grid_coordinates(nx, dx, ny, dy, nz, dz, self.ndims)
        self._obs_coords = _obs_interp_coords(self.obs_locations, dx, dy, dz, self.ndims)

        # Schur complement scalars — O(n_obs) only, no grid-sized arrays stored.
        ones = np.ones(n_obs)
        self._alpha = scipy.linalg.cho_solve(self._cho_factor, ones)  # (n_obs,)  C^{-1} 1
        self._s = float(ones @ self._alpha)                           # scalar    1^T C^{-1} 1

        # BLUE estimate of the unknown constant mean: mu_hat = (1^T C^{-1} z) / s
        gamma = scipy.linalg.cho_solve(self._cho_factor, self.obs_values)
        self.estimated_mean: float = float(ones @ gamma / self._s)

    def _ok_weights_chunk(self, K):
        """Return OK weights for a chunk K (chunk_size, n_obs) -> w (n_obs, chunk_size)."""
        beta = scipy.linalg.cho_solve(self._cho_factor, K.T)              # (n_obs, cs)
        drift = (self._alpha @ K.T - 1.0) / self._s                      # (cs,)
        return beta - np.outer(self._alpha, drift), drift

    def predict(self):
        n_grid = self._grid_coords.shape[0]
        n_obs = len(self.obs_locations)
        chunk = _chunk_size(n_grid, n_obs)
        kriging_mean_flat = np.empty(n_grid)
        kriging_var_flat = np.empty(n_grid)

        for start in range(0, n_grid, chunk):
            end = min(start + chunk, n_grid)
            K = _build_cov_chunk(self.variogram, self._grid_coords, start, end,
                                 self.obs_locations, self.ndims)           # (cs, n_obs)
            w, drift = self._ok_weights_chunk(K)                          # (n_obs, cs), (cs,)
            kriging_mean_flat[start:end] = w.T @ self.obs_values
            kriging_var_flat[start:end] = 1.0 - np.sum(K * w.T, axis=1) - drift

        kriging_mean = kriging_mean_flat.reshape(self._grid_shape)
        kriging_stdev = np.sqrt(np.maximum(kriging_var_flat, 0.0)).reshape(self._grid_shape)
        return kriging_mean, kriging_stdev

    def simulate(self, n_sim=1):
        n_grid = self._grid_coords.shape[0]
        n_obs = len(self.obs_locations)
        chunk = _chunk_size(n_grid, n_obs)
        results = []

        for _ in range(n_sim):
            uncond = _simulate_uncond(
                self.variogram, self.nx, self.dx, self.ny, self.dy,
                self.nz, self.dz, self._grid_shape, self.ndims
            )
            uncond_at_obs = _interpolate_at_obs(uncond, self._obs_coords)
            obs_residuals = self.obs_values - uncond_at_obs

            correction_flat = np.empty(n_grid)
            for start in range(0, n_grid, chunk):
                end = min(start + chunk, n_grid)
                K = _build_cov_chunk(self.variogram, self._grid_coords, start, end,
                                     self.obs_locations, self.ndims)
                w, _ = self._ok_weights_chunk(K)
                correction_flat[start:end] = w.T @ obs_residuals

            results.append(uncond + correction_flat.reshape(self._grid_shape))
        return results
