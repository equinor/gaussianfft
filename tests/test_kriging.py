import platform

import numpy as np
import pytest

from gaussianfft._kriging.grid_spec import GridSpec

if platform.python_implementation() == 'PyPy':
    pytest.skip('Kriging requires SciPy, which is unavailable on PyPy', allow_module_level=True)

import gaussianfft as grf
from gaussianfft._kriging import (
    ObservationData,
    OrdinaryKriging,
    Variogram,
    kriging_toolkit,
    predict,
)


@pytest.mark.parametrize("kwargs", [
    # Shape is a 1-3D tuple of positive integers
    {"shape": ()},
    {"shape": (2, 2, 2, 2)},
    {"shape": (None,)},
    {"shape": (np.bool_(True),)},

    # Spacing must be positive and finite
    {"spacing": [0.0]},
    {"spacing": [-1.0]},
    {"spacing": [np.nan]},
    {"spacing": [np.inf]},

    # Inconsistent spacing/shape/origin dimensions
    {"shape": (2,), "spacing": [1.0, 1.0], "origin": [0.0]},
    {"shape": (2,), "spacing": [1.0], "origin": [0.0, 0.0]},
    {"shape": (2, 3), "spacing": [1.0], "origin": [0.0]},
])
def test_grid_spec_rejects_invalid_inputs(kwargs):
    inputs = {"shape": (2,), "spacing": [1.0], "origin": [0.0]}
    inputs.update(kwargs)

    with pytest.raises(ValueError):
        GridSpec(**inputs)


@pytest.mark.parametrize("kwargs", [
    # Locations must be a 2D array with 1-3 coordinates per observation
    {"locations": [0.0]},
    {"locations": [[]]},
    {"locations": [[0.0, 0.0, 0.0, 0.0]]},

    # All observations must have the same number of coordinates
    {"locations": [[0.0, 1.0], [2.0]], "values": [1.0, 2.0], "uncertainties": [0.0, 0.0]},

    # At least one observation is required
    {"locations": np.empty((0, 1)), "values": [], "uncertainties": []},

    # Inconsistent locations/values/uncertainties counts
    {"locations": [[0.0], [1.0]], "values": [1.0], "uncertainties": [0.0]},
    {"locations": [[0.0]], "values": [1.0, 2.0], "uncertainties": [0.0]},
    {"locations": [[0.0]], "values": [1.0], "uncertainties": [0.0, 0.0]},

    # Uncertainties must be non-negative
    {"uncertainties": [-0.1]},
])
def test_observation_data_rejects_invalid_inputs(kwargs):
    inputs = {"locations": [[0.0]], "values": [1.0], "uncertainties": [0.0]}
    inputs.update(kwargs)

    with pytest.raises(ValueError):
        ObservationData(**inputs)


@pytest.mark.parametrize("field", ["locations", "values", "uncertainties"])
@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_observation_data_rejects_nonfinite_inputs(field, value):
    inputs = {"locations": [[0.0]], "values": [1.0], "uncertainties": [0.0]}
    inputs[field] = [[value]] if field == "locations" else [value]

    with pytest.raises(ValueError):
        ObservationData(**inputs)


# ---------------------------------------------------------------------------
# Simple Kriging
# ---------------------------------------------------------------------------

def _explicit_sample(rng: np.random.Generator, locations: np.ndarray, variogram: grf.Variogram,n_samples: int) -> np.ndarray:
    """Build C_ij = rho(x_i - x_j), then sample F = mean + Z L^T for C = L L^T."""

    displacements = locations[:, None, :] - locations[None, :, :]
    covariance = np.array([
        [variogram.corr(dx, dy) for dx, dy in displacement_row]
        for displacement_row in displacements
    ])
    factor = np.linalg.cholesky(covariance)
    return rng.standard_normal((n_samples, len(covariance))) @ factor.T


@pytest.mark.parametrize(
    "variogram_type",
    [kind for kind in grf.VariogramType if kind is not grf.VariogramType.CONSTANT],
    ids=lambda kind: kind.value,
)
@pytest.mark.parametrize("range_y", [12.0, 6.0], ids=["isotropic", "anisotropic"])
def test_simple_kriging_calibrated_on_independent_gaussian_fields(variogram_type, range_y):
    """Independent Gaussian draws should give unbiased, calibrated prediction errors."""
    rng = np.random.default_rng(20261102)
    grid_shape = (6, 5)
    grid_spacing = (2.0, 3.0)
    grid_locations = np.array([
        [ix * grid_spacing[0], iy * grid_spacing[1]]
        for ix in range(grid_shape[0]) for iy in range(grid_shape[1])
    ])
    obs_locations = np.array([[0.5, 1.0], [3.0, 7.0], [8.5, 10.0]])
    obs_uncertainties = np.array([0.1, 0.3, 0.5])
    locations = np.concatenate((grid_locations, obs_locations))

    range_x = 12.0
    mean = 2.5
    n_samples = 2048
    variogram = grf.variogram(variogram_type, range_x, range_y)
    fields = mean + _explicit_sample(rng, locations, variogram, n_samples)

    n_grid = len(grid_locations)
    true_fields = fields[:, :n_grid].reshape((n_samples, *grid_shape))
    observations = fields[:, n_grid:] + rng.standard_normal(
        (n_samples, len(obs_locations)),
    ) * obs_uncertainties
    standardized_errors = np.empty_like(true_fields)

    for sample_idx in range(n_samples):
        prediction, stddev = predict(
            variogram, grid_shape, grid_spacing,
            obs_locations, observations[sample_idx], obs_uncertainties,
            mean=mean, calculate_stddev=True,
        )
        assert stddev is not None
        assert prediction.shape == stddev.shape == grid_shape
        assert np.all(stddev > 0)
        standardized_errors[sample_idx] = (prediction - true_fields[sample_idx]) / stddev

    mean_error = standardized_errors.mean(axis=0)
    error_variance = standardized_errors.var(axis=0, ddof=1)

    # Bounds should be within 5 SE of expected in each of the 840 cases at ~5.7e-7/check (~0.05% for 14*30 checks had they been independent)
    np.testing.assert_allclose(mean_error, 0.0, rtol=0, atol=5 / np.sqrt(n_samples))
    np.testing.assert_allclose(error_variance, 1.0, rtol=0, atol=5 * np.sqrt(2 / (n_samples - 1)))


class TestSimpleKriging1D:
    def setup_method(self):
        self.variogram = grf.variogram('exponential', 100.0)
        self.nx = 50
        self.dx = 5.0

    def test_exact_interpolation_zero_uncertainty(self):
        obs_locations = np.array([[50.0], [100.0], [150.0]])
        obs_values = np.array([1.0, -0.5, 0.8])
        obs_uncertainties = np.array([0.0, 0.0, 0.0])

        mean_field, variance_field = predict(
            self.variogram, (self.nx,), (self.dx,),
            obs_locations, obs_values, obs_uncertainties,
        )

        assert mean_field.shape == (self.nx,)
        # At observation nodes, kriging mean should match obs values
        for loc, val in zip(obs_locations, obs_values):
            idx = int(round(loc[0] / self.dx))
            assert abs(mean_field[idx] - val) < 1e-6

    def test_stdev_near_zero_at_obs_no_uncertainty(self):
        obs_locations = np.array([[50.0], [100.0], [150.0]])
        obs_values = np.array([1.0, -0.5, 0.8])
        obs_uncertainties = np.array([0.0, 0.0, 0.0])

        _, stdev_field = predict(
            self.variogram, (self.nx,), (self.dx,),
            obs_locations, obs_values, obs_uncertainties,
            calculate_stddev=True,
        )

        for loc in obs_locations:
            idx = int(round(loc[0] / self.dx))
            # Numerical jitter in covariance regularization is 1e-10, so stdev is ~1e-5.
            assert stdev_field[idx] < 2e-5

    def test_stdev_increases_away_from_obs(self):
        obs_locations = np.array([[100.0]])
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])

        _, stdev_field = predict(
            self.variogram, (self.nx,), (self.dx,),
            obs_locations, obs_values, obs_uncertainties,
            calculate_stddev=True,
        )

        idx_obs = int(round(100.0 / self.dx))
        # Stdev should be larger far from the observation.
        assert stdev_field[0] > stdev_field[idx_obs]
        assert stdev_field[-1] > stdev_field[idx_obs]

    def test_nonzero_mean(self):
        obs_locations = np.array([[50.0]])
        obs_values = np.array([5.0])
        obs_uncertainties = np.array([0.0])

        mean_field, _ = predict(
            self.variogram, (self.nx,), (self.dx,),
            obs_locations, obs_values, obs_uncertainties,
            mean=3.0,
        )

        # At observation, should equal obs value
        idx = int(round(50.0 / self.dx))
        assert abs(mean_field[idx] - 5.0) < 1e-6
        # Far from observation, should tend toward the mean
        # (at distance >> range, kriging mean = prior mean)
        assert abs(mean_field[0] - 3.0) < abs(mean_field[0] - 5.0)

    def test_conditional_simulation_statistics(self):
        grf.seed(42)
        obs_locations = np.array([[50.0], [150.0]])
        obs_values = np.array([1.0, -0.5])
        obs_uncertainties = np.array([0.0, 0.0])

        n_sims = 100
        sims = grf.conditional_simulate(
            self.variogram, (self.nx,), (self.dx,),
            obs_locations, obs_values, obs_uncertainties,
            n=n_sims,
        )

        assert len(sims) == n_sims
        assert sims[0].shape == (self.nx,)

        # At observation locations, all simulations should match obs values
        for sim in sims:
            idx0 = int(round(50.0 / self.dx))
            idx1 = int(round(150.0 / self.dx))
            assert abs(sim[idx0] - 1.0) < 1e-4
            assert abs(sim[idx1] - (-0.5)) < 1e-4

    def test_conditional_simulation_stdev(self):
        grf.seed(123)
        obs_locations = np.array([[100.0]])
        obs_values = np.array([0.0])
        obs_uncertainties = np.array([0.0])

        _, kriging_std = predict(
            self.variogram, (self.nx,), (self.dx,),
            obs_locations, obs_values, obs_uncertainties,
            calculate_stddev=True,
        )

        n_sims = 200
        sims = grf.conditional_simulate(
            self.variogram, (self.nx,), (self.dx,),
            obs_locations, obs_values, obs_uncertainties,
            n=n_sims,
        )

        sim_stack = np.array(sims)
        empirical_var = np.var(sim_stack, axis=0)

        empirical_std = np.sqrt(empirical_var)

        # Empirical std should approximate kriging std
        # (statistical test, use generous tolerance)
        rel_error = np.abs(empirical_std - kriging_std) / np.maximum(kriging_std, 0.1)
        # Most points should have reasonable agreement
        assert np.median(rel_error) < 0.5


class TestSimpleKriging2D:
    def setup_method(self):
        self.variogram = grf.variogram('exponential', 50.0, 50.0)
        self.nx = 20
        self.dx = 5.0
        self.ny = 20
        self.dy = 5.0

    def test_exact_interpolation(self):
        obs_locations = np.array([[25.0, 25.0], [50.0, 50.0]])
        obs_values = np.array([1.5, -1.0])
        obs_uncertainties = np.array([0.0, 0.0])

        mean_field, _ = predict(
            self.variogram, (self.nx, self.ny), (self.dx, self.dy),
            obs_locations, obs_values, obs_uncertainties,
            calculate_stddev=False,
        )

        assert mean_field.shape == (self.nx, self.ny)

        # Check exact interpolation
        for loc, val in zip(obs_locations, obs_values):
            ix = int(round(loc[0] / self.dx))
            iy = int(round(loc[1] / self.dy))
            assert abs(mean_field[ix, iy] - val) < 1e-6

    def test_stdev_at_obs(self):
        obs_locations = np.array([[25.0, 25.0]])
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])

        _, stddev_field = predict(
            self.variogram, (self.nx, self.ny), (self.dx, self.dy),
            obs_locations, obs_values, obs_uncertainties,
            calculate_stddev=True,
        )

        ix = int(round(25.0 / self.dx))
        iy = int(round(25.0 / self.dy))
        assert stddev_field[ix, iy] < 2e-5
        # Corner should have higher stdev
        assert stddev_field[0, 0] > stddev_field[ix, iy]

    def test_conditional_simulation_with_scalar_mean(self):
        grf.seed(123)
        obs_locations = np.array([[25.0, 25.0], [50.0, 50.0]])
        obs_values = np.array([1.5, -1.0])
        obs_uncertainties = np.array([0.0, 0.0])
        mean = 2.0

        sims = grf.conditional_simulate(
            self.variogram, (self.nx, self.ny), (self.dx, self.dy),
            obs_locations, obs_values, obs_uncertainties,
            mean=mean, n=1,
        )

        assert len(sims) == 1
        assert sims[0].shape == (self.nx, self.ny)
        for loc, val in zip(obs_locations, obs_values):
            ix = int(round(loc[0] / self.dx))
            iy = int(round(loc[1] / self.dy))
            assert abs(sims[0][ix, iy] - val) < 1e-4


class TestSimpleKriging3D:
    def setup_method(self):
        self.variogram = grf.variogram('exponential', 30.0, 30.0, 30.0)
        self.nx, self.dx = 10, 5.0
        self.ny, self.dy = 10, 5.0
        self.nz, self.dz = 10, 5.0

    def test_exact_interpolation(self):
        obs_locations = np.array([[20.0, 20.0, 20.0]])
        obs_values = np.array([2.0])
        obs_uncertainties = np.array([0.0])

        mean_field, _ = predict(
            self.variogram, (self.nx, self.ny, self.nz), (self.dx, self.dy, self.dz),
            obs_locations, obs_values, obs_uncertainties,
        )

        assert mean_field.shape == (self.nx, self.ny, self.nz)
        ix = int(round(20.0 / self.dx))
        iy = int(round(20.0 / self.dy))
        iz = int(round(20.0 / self.dz))
        assert abs(mean_field[ix, iy, iz] - 2.0) < 1e-6


class TestInputValidation:
    """Input validation applies to both methods; tested via SimpleKriging (default)."""
    def setup_method(self):
        self.variogram = grf.variogram('exponential', 100.0)

    def test_shape_mismatch_values(self):
        obs_locations = np.array([[10.0], [20.0]])
        obs_values = np.array([1.0, 2.0, 3.0])  # Wrong shape
        obs_uncertainties = np.array([0.0, 0.0])

        with pytest.raises(ValueError, match="obs_values"):
            predict(self.variogram, (50,), (5.0,), obs_locations, obs_values, obs_uncertainties)

    def test_shape_mismatch_uncertainties(self):
        obs_locations = np.array([[10.0], [20.0]])
        obs_values = np.array([1.0, 2.0])
        obs_uncertainties = np.array([0.0])  # Wrong shape

        with pytest.raises(ValueError, match="obs_uncertainties"):
            predict(self.variogram, (50,), (5.0,), obs_locations, obs_values, obs_uncertainties)

    def test_negative_uncertainties(self):
        obs_locations = np.array([[10.0], [20.0]])
        obs_values = np.array([1.0, 2.0])
        obs_uncertainties = np.array([0.1, -0.1])  # Negative

        with pytest.raises(ValueError, match="non-negative"):
            predict(self.variogram, (50,), (5.0,), obs_locations, obs_values, obs_uncertainties)

    def test_simulation_obs_out_of_bounds(self):
        obs_locations = np.array([[300.0]])  # Beyond grid (50 * 5.0 = 245 max)
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])

        with pytest.raises(ValueError, match="outside grid bounds"):
            grf.conditional_simulate(
                self.variogram, (50,), (5.0,), obs_locations, obs_values, obs_uncertainties,
            )

    def test_unexpected_keyword_argument(self):
        obs_locations = np.array([[10.0]])
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])

        with pytest.raises(TypeError, match="unexpected keyword argument"):
            # Intentional invalid-keyword call to verify runtime validation.
            predict(self.variogram, (50,), (5.0,), obs_locations, obs_values, obs_uncertainties, typo=True)  # type: ignore[reportCallIssue]

    def test_mismatched_grid_spacing_rejected(self):
        obs_locations = np.array([[10.0]])
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])

        with pytest.raises(ValueError, match="same length"):
            predict(self.variogram, (50, 20), (5.0,), obs_locations, obs_values, obs_uncertainties)

    def test_wrong_ndims_in_locations(self):
        # 1D grid but 2D observation locations
        obs_locations = np.array([[10.0, 20.0]])
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])

        with pytest.raises(ValueError, match="columns"):
            predict(self.variogram, (50,), (5.0,), obs_locations, obs_values, obs_uncertainties)

    def test_1d_obs_locations_rejected(self):
        obs_locations = np.array([10.0, 20.0])  # 1D array, needs to be 2D
        obs_values = np.array([1.0, 2.0])
        obs_uncertainties = np.array([0.0, 0.0])

        with pytest.raises(ValueError, match="2D"):
            predict(self.variogram, (50,), (5.0,), obs_locations, obs_values, obs_uncertainties)


# ---------------------------------------------------------------------------
# Ordinary Kriging
# ---------------------------------------------------------------------------

class TestOrdinaryKriging1D:
    def setup_method(self):
        self.variogram = grf.variogram('exponential', 100.0)
        self.nx = 50
        self.dx = 5.0

    def _predict(self, obs_locations, obs_values, obs_uncertainties, **kwargs):
        return predict(
            self.variogram, (self.nx,), (self.dx,),
            obs_locations, obs_values, obs_uncertainties,
            method='ordinary', **kwargs,
        )

    def test_exact_interpolation_zero_uncertainty(self):
        obs_locations = np.array([[50.0], [100.0], [150.0]])
        obs_values = np.array([1.0, -0.5, 0.8])
        obs_uncertainties = np.array([0.0, 0.0, 0.0])

        mean_field, _ = self._predict(obs_locations, obs_values, obs_uncertainties)

        assert mean_field.shape == (self.nx,)
        for loc, val in zip(obs_locations, obs_values):
            idx = int(round(loc[0] / self.dx))
            assert abs(mean_field[idx] - val) < 1e-6

    def test_stdev_near_zero_at_obs(self):
        obs_locations = np.array([[50.0], [100.0], [150.0]])
        obs_values = np.array([1.0, -0.5, 0.8])
        obs_uncertainties = np.array([0.0, 0.0, 0.0])

        _, stdev_field = self._predict(obs_locations, obs_values, obs_uncertainties, calculate_stddev=True)

        for loc in obs_locations:
            idx = int(round(loc[0] / self.dx))
            assert stdev_field[idx] < 2e-5

    def test_constant_observations_mean_converges_to_constant(self):
        # With all obs = same value and range << grid, OK mean should equal that value
        obs_locations = np.array([[50.0], [100.0], [150.0], [200.0]])
        obs_values = np.full(4, 3.0)
        obs_uncertainties = np.zeros(4)

        mean_field, _ = self._predict(obs_locations, obs_values, obs_uncertainties)

        # Within the data neighbourhood the estimate should stay close to 3.0
        np.testing.assert_allclose(mean_field[10:40], 3.0, atol=0.05)

    def test_stdev_increases_away_from_obs(self):
        obs_locations = np.array([[100.0]])
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])

        _, stdev_field = self._predict(obs_locations, obs_values, obs_uncertainties, calculate_stddev=True)

        idx_obs = int(round(100.0 / self.dx))
        assert stdev_field[0] > stdev_field[idx_obs]
        assert stdev_field[-1] > stdev_field[idx_obs]

    def test_conditional_simulation_honors_observations(self):
        grf.seed(42)
        obs_locations = np.array([[50.0], [150.0]])
        obs_values = np.array([1.0, -0.5])
        obs_uncertainties = np.array([0.0, 0.0])

        sims = grf.conditional_simulate(
            self.variogram, (self.nx,), (self.dx,),
            obs_locations, obs_values, obs_uncertainties,
            n=50, method='ordinary',
        )

        assert len(sims) == 50
        assert sims[0].shape == (self.nx,)
        for sim in sims:
            idx0 = int(round(50.0 / self.dx))
            idx1 = int(round(150.0 / self.dx))
            assert abs(sim[idx0] - 1.0) < 1e-4
            assert abs(sim[idx1] - (-0.5)) < 1e-4

    def test_estimated_mean_constant_observations(self):
        # When all obs values are the same constant, estimated_mean should equal it
        obs_locations = np.array([[50.0], [100.0], [150.0]])
        obs_values = np.full(3, 4.0)
        obs_uncertainties = np.zeros(3)

        obs = ObservationData(obs_locations, obs_values, obs_uncertainties)
        ok = OrdinaryKriging()
        ok.predict(GridSpec((self.nx,), (self.dx,)), obs, Variogram(self.variogram))

        assert abs(ok.estimated_mean - 4.0) < 1e-6

class TestOrdinaryKriging2D:
    def setup_method(self):
        self.variogram = grf.variogram('exponential', 50.0, 50.0)
        self.nx, self.dx = 20, 5.0
        self.ny, self.dy = 20, 5.0

    def test_exact_interpolation(self):
        obs_locations = np.array([[25.0, 25.0], [50.0, 50.0]])
        obs_values = np.array([1.5, -1.0])
        obs_uncertainties = np.array([0.0, 0.0])

        mean_field, _ = predict(
            self.variogram, (self.nx, self.ny), (self.dx, self.dy),
            obs_locations, obs_values, obs_uncertainties,
            method='ordinary',
        )

        assert mean_field.shape == (self.nx, self.ny)
        for loc, val in zip(obs_locations, obs_values):
            ix = int(round(loc[0] / self.dx))
            iy = int(round(loc[1] / self.dy))
            assert abs(mean_field[ix, iy] - val) < 1e-6


@pytest.mark.parametrize("method", ["simple", "ordinary"])
@pytest.mark.parametrize("calculate_stddev", [False, True])
@pytest.mark.parametrize("variogram_type", ["exponential", "gaussian", "spherical"])
def test_chunked_prediction_matches_single_batch(
    monkeypatch, method, calculate_stddev, variogram_type,
):
    variogram = grf.variogram(variogram_type, 20.0, 30.0)
    args = (
        variogram, (3, 5), (2.0, 3.0),
        [[0.5, 1.0], [3.0, 7.0], [1.0, 10.0]],
        [1.0, -0.5, 2.0], [0.1, 0.2, 0.1],
    )
    batch_sizes = []
    corr_matrix = Variogram.corr_matrix
    skip_observation_covariance = True

    # Observing internals is not great test practice, but it allows us to verify that chunking happens
    def record_batch(covariance, points, locations):
        nonlocal skip_observation_covariance
        if skip_observation_covariance:
            skip_observation_covariance = False
        else:
            batch_sizes.append(len(points))
        return corr_matrix(covariance, points, locations)

    monkeypatch.setattr(Variogram, "corr_matrix", record_batch)
    monkeypatch.setattr(kriging_toolkit, "_MEMORY_BUDGET_BYTES", 1024 * 1024)
    expected_mean, expected_stddev = predict(
        *args, method=method, calculate_stddev=calculate_stddev,
    )
    assert len(batch_sizes) == 1
    assert sum(batch_sizes) == 15
    batch_sizes.clear()
    skip_observation_covariance = True

    # Budget for four grid points, three observations, and four float64 arrays.
    monkeypatch.setattr(kriging_toolkit, "_MEMORY_BUDGET_BYTES", 4 * 3 * 4 * 8)
    actual_mean, actual_stddev = predict(
        *args, method=method, calculate_stddev=calculate_stddev,
    )

    assert len(batch_sizes) > 1
    assert all(0 < size <= 4 for size in batch_sizes)
    assert sum(batch_sizes) == 15
    assert actual_mean.shape == (3, 5)

    # Verify that the predicted mean and standard deviation match the expected values up to numerical error
    np.testing.assert_allclose(actual_mean, expected_mean, rtol=1e-12, atol=1e-12)
    if calculate_stddev:
        assert actual_stddev is not None
        assert expected_stddev is not None
        assert actual_stddev.shape == (3, 5)
        np.testing.assert_allclose(actual_stddev, expected_stddev, rtol=1e-12, atol=1e-12)
    else:
        assert actual_stddev is expected_stddev is None


# ---------------------------------------------------------------------------
# Method dispatch
# ---------------------------------------------------------------------------

class TestMethodDispatch:
    def setup_method(self):
        self.variogram = grf.variogram('exponential', 100.0)
        self.nx, self.dx = 20, 5.0
        self.obs_locations = np.array([[25.0], [75.0]])
        self.obs_values = np.array([1.0, 3.0])   # non-zero mean → SK(mean=0) ≠ OK
        self.obs_uncertainties = np.array([0.0, 0.0])

    def _args(self):
        return (self.variogram, (self.nx,), (self.dx,),
                self.obs_locations, self.obs_values, self.obs_uncertainties)

    @pytest.mark.parametrize("predict_fn", [predict, grf.predict])
    def test_default_is_simple_kriging(self, predict_fn):
        mean_default, _ = predict_fn(*self._args())
        mean_sk, _ = predict_fn(*self._args(), method='simple')
        np.testing.assert_array_equal(mean_default, mean_sk)

    @pytest.mark.parametrize("predict_fn", [predict, grf.predict])
    def test_ok_and_sk_differ(self, predict_fn):
        mean_sk, _ = predict_fn(*self._args(), method='simple')
        mean_ok, _ = predict_fn(*self._args(), method='ordinary')
        # SK and OK should generally differ (different assumptions about the mean)
        assert not np.allclose(mean_sk, mean_ok)

    @pytest.mark.parametrize("method", ['UnknownMethod', 'SimpleKriging', 'OrdinaryKriging'])
    @pytest.mark.parametrize("kriging_fn", [predict, grf.predict, grf.conditional_simulate])
    def test_invalid_method_raises(self, method, kriging_fn):
        with pytest.raises(ValueError, match="Unknown kriging method"):
            kriging_fn(*self._args(), method=method)

    def test_conditional_simulate_default_is_simple_kriging(self):
        sims_default = grf.conditional_simulate(*self._args(), n=5, seed=0)
        sims_sk = grf.conditional_simulate(*self._args(), n=5, seed=0, method='simple')
        np.testing.assert_array_equal(sims_default, sims_sk)

    def test_conditional_simulate_method_dispatch(self):
        grf.seed(0)
        sims_sk = grf.conditional_simulate(*self._args(), n=5, method='simple')
        grf.seed(0)
        sims_ok = grf.conditional_simulate(*self._args(), n=5, method='ordinary')
        # Results from different methods should differ
        assert not np.allclose(sims_sk[0], sims_ok[0])
