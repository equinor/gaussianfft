import numpy as np
import pytest

import gaussianfft as grf
from gaussianfft._kriging import predict
from gaussianfft._kriging.kriging_toolkit import OrdinaryKriging


# ---------------------------------------------------------------------------
# Simple Kriging
# ---------------------------------------------------------------------------

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
            self.variogram, self.nx, self.dx,
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
            self.variogram, self.nx, self.dx,
            obs_locations, obs_values, obs_uncertainties,
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
            self.variogram, self.nx, self.dx,
            obs_locations, obs_values, obs_uncertainties,
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
            self.variogram, self.nx, self.dx,
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
            self.variogram, self.nx, self.dx,
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
            self.variogram, self.nx, self.dx,
            obs_locations, obs_values, obs_uncertainties,
        )

        n_sims = 200
        sims = grf.conditional_simulate(
            self.variogram, self.nx, self.dx,
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

        mean_field, variance_field = predict(
            self.variogram, self.nx, self.dx,
            obs_locations, obs_values, obs_uncertainties,
            ny=self.ny, dy=self.dy,
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

        _, stdev_field = predict(
            self.variogram, self.nx, self.dx,
            obs_locations, obs_values, obs_uncertainties,
            ny=self.ny, dy=self.dy,
        )

        ix = int(round(25.0 / self.dx))
        iy = int(round(25.0 / self.dy))
        assert stdev_field[ix, iy] < 2e-5
        # Corner should have higher stdev
        assert stdev_field[0, 0] > stdev_field[ix, iy]

    def test_conditional_simulation_with_array_mean(self):
        grf.seed(123)
        obs_locations = np.array([[25.0, 25.0], [50.0, 50.0]])
        obs_values = np.array([1.5, -1.0])
        obs_uncertainties = np.array([0.0, 0.0])
        mean = np.zeros((self.nx, self.ny))

        sims = grf.conditional_simulate(
            self.variogram, self.nx, self.dx, self.ny, self.dy,
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
            self.variogram, self.nx, self.dx,
            obs_locations, obs_values, obs_uncertainties,
            ny=self.ny, dy=self.dy, nz=self.nz, dz=self.dz,
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
            predict(self.variogram, 50, 5.0, obs_locations, obs_values, obs_uncertainties)

    def test_shape_mismatch_uncertainties(self):
        obs_locations = np.array([[10.0], [20.0]])
        obs_values = np.array([1.0, 2.0])
        obs_uncertainties = np.array([0.0])  # Wrong shape

        with pytest.raises(ValueError, match="obs_uncertainties"):
            predict(self.variogram, 50, 5.0, obs_locations, obs_values, obs_uncertainties)

    def test_negative_uncertainties(self):
        obs_locations = np.array([[10.0], [20.0]])
        obs_values = np.array([1.0, 2.0])
        obs_uncertainties = np.array([0.1, -0.1])  # Negative

        with pytest.raises(ValueError, match="non-negative"):
            predict(self.variogram, 50, 5.0, obs_locations, obs_values, obs_uncertainties)

    def test_obs_out_of_bounds(self):
        obs_locations = np.array([[300.0]])  # Beyond grid (50 * 5.0 = 245 max)
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])

        with pytest.raises(ValueError, match="outside grid bounds"):
            predict(self.variogram, 50, 5.0, obs_locations, obs_values, obs_uncertainties)

    def test_array_mean_shape_mismatch(self):
        obs_locations = np.array([[10.0]])
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])
        mean = np.zeros((2, 2))

        with pytest.raises(ValueError, match="mean"):
            predict(self.variogram, 50, 5.0, obs_locations, obs_values, obs_uncertainties, mean=mean)

    def test_unexpected_keyword_argument(self):
        obs_locations = np.array([[10.0]])
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])

        with pytest.raises(TypeError, match="unexpected keyword argument"):
            predict(self.variogram, 50, 5.0, obs_locations, obs_values, obs_uncertainties, typo=True)

    def test_partial_keyword_grid_rejected(self):
        obs_locations = np.array([[10.0]])
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])

        with pytest.raises(TypeError, match="ny must be provided"):
            predict(self.variogram, 50, 5.0, obs_locations, obs_values, obs_uncertainties, dy=5.0)

    def test_wrong_ndims_in_locations(self):
        # 1D grid but 2D observation locations
        obs_locations = np.array([[10.0, 20.0]])
        obs_values = np.array([1.0])
        obs_uncertainties = np.array([0.0])

        with pytest.raises(ValueError, match="columns"):
            predict(self.variogram, 50, 5.0, obs_locations, obs_values, obs_uncertainties)

    def test_1d_obs_locations_rejected(self):
        obs_locations = np.array([10.0, 20.0])  # 1D array, needs to be 2D
        obs_values = np.array([1.0, 2.0])
        obs_uncertainties = np.array([0.0, 0.0])

        with pytest.raises(ValueError, match="2D"):
            predict(self.variogram, 50, 5.0, obs_locations, obs_values, obs_uncertainties)


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
            self.variogram, self.nx, self.dx,
            obs_locations, obs_values, obs_uncertainties,
            method='OrdinaryKriging', **kwargs,
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

        _, stdev_field = self._predict(obs_locations, obs_values, obs_uncertainties)

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

        _, stdev_field = self._predict(obs_locations, obs_values, obs_uncertainties)

        idx_obs = int(round(100.0 / self.dx))
        assert stdev_field[0] > stdev_field[idx_obs]
        assert stdev_field[-1] > stdev_field[idx_obs]

    def test_conditional_simulation_honors_observations(self):
        grf.seed(42)
        obs_locations = np.array([[50.0], [150.0]])
        obs_values = np.array([1.0, -0.5])
        obs_uncertainties = np.array([0.0, 0.0])

        sims = grf.conditional_simulate(
            self.variogram, self.nx, self.dx,
            obs_locations, obs_values, obs_uncertainties,
            n=50, method='OrdinaryKriging',
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

        ok = OrdinaryKriging(
            self.variogram, self.nx, self.dx, 1, 1.0, 1, 1.0,
            obs_locations, obs_values, obs_uncertainties,
        )

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
            self.variogram, self.nx, self.dx,
            obs_locations, obs_values, obs_uncertainties,
            ny=self.ny, dy=self.dy, method='OrdinaryKriging',
        )

        assert mean_field.shape == (self.nx, self.ny)
        for loc, val in zip(obs_locations, obs_values):
            ix = int(round(loc[0] / self.dx))
            iy = int(round(loc[1] / self.dy))
            assert abs(mean_field[ix, iy] - val) < 1e-6


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
        return (self.variogram, self.nx, self.dx,
                self.obs_locations, self.obs_values, self.obs_uncertainties)

    def test_default_is_simple_kriging(self):
        mean_default, _ = predict(*self._args())
        mean_sk, _ = predict(*self._args(), method='SimpleKriging')
        np.testing.assert_array_equal(mean_default, mean_sk)

    def test_ok_and_sk_differ(self):
        mean_sk, _ = predict(*self._args(), method='SimpleKriging')
        mean_ok, _ = predict(*self._args(), method='OrdinaryKriging')
        # SK and OK should generally differ (different assumptions about the mean)
        assert not np.allclose(mean_sk, mean_ok)

    def test_invalid_method_raises(self):
        with pytest.raises(ValueError, match="Unknown kriging method"):
            predict(*self._args(), method='UnknownMethod')

    def test_conditional_simulate_method_dispatch(self):
        grf.seed(0)
        sims_sk = grf.conditional_simulate(*self._args(), n=5, method='SimpleKriging')
        grf.seed(0)
        sims_ok = grf.conditional_simulate(*self._args(), n=5, method='OrdinaryKriging')
        # Results from different methods should differ
        assert not np.allclose(sims_sk[0], sims_ok[0])
