import platform

import numpy as np
import pytest

if platform.python_implementation() == 'PyPy':
    pytest.skip('Kriging requires SciPy, which is unavailable on PyPy', allow_module_level=True)

import scipy.linalg

import gaussianfft as grf
from gaussianfft._kriging import (
    GridSpec, GriddedAzimuth, NonstationaryVariogram, ObservationData, OrdinaryKriging,
    SimpleKriging, Variogram, predict,
)


def swirl_azimuth(locations):
    angle = np.degrees(np.arctan2(locations[:, 1] - 150.0, locations[:, 0] - 200.0))
    return (angle + 90.0) % 360.0


class TestVariogram:
    def test_corr_matrix_matches_corr_array(self):
        variogram = Variogram.from_parameters('matern52', 200.0, 50.0, azimuth=30.0)
        reference = grf.variogram('matern52', main_range=200.0, perp_range=50.0, azimuth=30.0)
        points = GridSpec((20, 15), (10.0, 10.0)).coordinates()
        locations = points[[0, 37, 299]]
        expected = np.stack([reference.corr_array(points - loc) for loc in locations], axis=1)
        np.testing.assert_allclose(variogram.corr_matrix(points, locations), expected)

    def test_wrapped_and_raw_variogram_give_same_prediction(self):
        raw = grf.variogram('exponential', 100.0)
        grid = GridSpec((30, 30), (5.0, 5.0))
        obs = ObservationData(np.array([[20.0, 20.0], [100.0, 60.0]]), np.array([1.0, -1.0]), np.zeros(2))
        expected, _ = predict(raw, grid.shape, grid.spacing, obs.locations, obs.values, obs.uncertainties)
        actual, _ = SimpleKriging().predict(grid, obs, Variogram(raw))
        np.testing.assert_array_equal(actual, expected)

    def test_simulation_equals_plain_fft(self):
        raw = grf.variogram('exponential', 100.0)
        grid = GridSpec((30, 20), (5.0, 5.0))
        grf.seed(5)
        expected = np.asarray(grf.simulate(raw, 30, 5.0, 20, 5.0)).reshape(grid.shape, order='F')
        grf.seed(5)
        np.testing.assert_array_equal(Variogram(raw).simulate(grid), expected)


class TestNonstationaryCorrelation:
    def setup_method(self):
        self.grid = GridSpec((40, 30), (10.0, 10.0))
        self.points = self.grid.coordinates()

    def test_constant_azimuth_on_bin_matches_stationary(self):
        nonstationary = NonstationaryVariogram(
            'matern52', 200.0, 50.0, azimuth=lambda p: np.full(len(p), 36.0), n_bins=100,
        )
        stationary = Variogram.from_parameters('matern52', 200.0, 50.0, azimuth=36.0)
        locations = self.points[[0, 517, 1199]]
        np.testing.assert_allclose(
            nonstationary.corr_matrix(self.points, locations),
            stationary.corr_matrix(self.points, locations), atol=1e-12,
        )
        obs = ObservationData(locations, np.array([1.0, -0.5, 0.8]), np.zeros(3))
        expected, _ = SimpleKriging().predict(self.grid, obs, stationary)
        actual, _ = SimpleKriging().predict(self.grid, obs, nonstationary)
        np.testing.assert_allclose(actual, expected, atol=1e-10)

    def test_unit_variance_including_wrap(self):
        azimuth = np.random.default_rng(1).uniform(0.0, 360.0, 50)
        azimuth[:2] = [359.9, -10.0]
        points = self.points[:50]
        variogram = NonstationaryVariogram(
            'exponential', 100.0, 30.0, azimuth=lambda p: azimuth[:len(p)],
        )
        np.testing.assert_allclose(np.diag(variogram.corr_matrix(points, points)), 1.0)

    def test_corr_matrix_is_symmetric_positive_definite(self):
        variogram = NonstationaryVariogram('matern52', 200.0, 50.0, azimuth=swirl_azimuth)
        idx = np.random.default_rng(3).choice(len(self.points), size=50, replace=False)
        locations = self.points[idx]
        corr = variogram.corr_matrix(locations, locations)
        np.testing.assert_allclose(corr, corr.T)
        scipy.linalg.cholesky(corr + 1e-10 * np.eye(len(corr)))

    def test_unrelated_azimuths_are_uncorrelated(self):
        variogram = NonstationaryVariogram(
            'exponential', 1000.0, azimuth=lambda p: np.where(p[:, 0] < 200.0, 0.0, 90.0),
        )
        corr = variogram.corr_matrix(np.array([[0.0, 0.0]]), np.array([[390.0, 0.0]]))
        assert corr[0, 0] == 0.0

    def test_invalid_azimuth_raises(self):
        variogram = NonstationaryVariogram('exponential', 100.0, azimuth=lambda p: np.full(len(p), np.nan))
        with pytest.raises(ValueError, match="finite"):
            variogram.weights(self.points[:3])


class TestNonstationarySimulation:
    def setup_method(self):
        self.grid = GridSpec((60, 60, 1), (10.0, 10.0, 1.0))
        self.variogram = NonstationaryVariogram(
            'matern52', 200.0, 50.0, azimuth=lambda p: 90.0 * p[:, 1] / 590.0, n_bins=36,
        )
        self.obs = ObservationData(
            np.array([[100.0, 100.0, 0.0], [300.0, 450.0, 0.0], [500.0, 200.0, 0.0]]),
            np.array([1.5, -1.0, 0.5]), np.zeros(3),
        )

    def test_unconditional_field(self):
        grf.seed(7)
        field = self.variogram.simulate(self.grid)
        assert field.shape == self.grid.shape
        assert np.all(np.isfinite(field))
        assert 0.3 < np.var(field) < 3.0

    @pytest.mark.parametrize('kriging', [SimpleKriging(), OrdinaryKriging()])
    def test_conditional_simulation_honours_observations(self, kriging):
        grf.seed(11)
        prediction, _ = kriging.predict(self.grid, self.obs, self.variogram)
        sims = kriging.simulate(self.grid, self.obs, self.variogram, n_sim=2)
        for loc, value in zip(self.obs.locations, self.obs.values):
            idx = tuple(np.rint(loc / self.grid.spacing).astype(int))
            assert abs(prediction[idx] - value) < 1e-6
            for sim in sims:
                assert abs(sim[idx] - value) < 1e-4


class TestGriddedAzimuth:
    def setup_method(self):
        self.grid = GridSpec((3, 2), (10.0, 10.0), origin=(100.0, 200.0))
        self.values = np.array([[359.0, 10.0], [1.0, 20.0], [90.0, 30.0]])
        self.azimuth = GriddedAzimuth(self.values, self.grid)

    def test_reproduces_node_values(self):
        np.testing.assert_allclose(
            self.azimuth(self.grid.coordinates()), self.values.ravel(), atol=1e-10,
        )

    def test_interpolates_across_wrap(self):
        midpoint = self.azimuth(np.array([[105.0, 200.0]]))[0]
        assert abs((midpoint + 180.0) % 360.0 - 180.0) < 1e-6

    def test_clamps_and_accepts_3d_locations(self):
        locations = np.array([[0.0, 0.0, 5.0], [1000.0, 1000.0, -5.0]])
        np.testing.assert_allclose(self.azimuth(locations), [359.0, 30.0], atol=1e-10)


class TestSharedNoise:
    def setup_method(self):
        self.grid = GridSpec((40, 40), (10.0, 10.0))
        self.points = self.grid.coordinates()
        self.variogram = NonstationaryVariogram(
            'matern52', 150.0, 40.0, azimuth=swirl_azimuth, n_bins=36, shared_noise=True,
        )
        self.obs = ObservationData(
            np.array([[100.0, 100.0], [300.0, 300.0]]), np.array([1.0, -1.0]), np.zeros(2),
        )

    def test_matches_empirical_covariance_of_simulations(self):
        idx = [np.ravel_multi_index(ij, self.grid.shape) for ij in [(20, 35), (5, 20), (30, 30)]]
        model = self.variogram.corr_matrix(self.points, self.points[idx])
        grf.seed(1)
        n = 300
        fields = np.array([self.variogram.simulate(self.grid).ravel() for _ in range(n)])
        empirical = fields.T @ fields[:, idx] / n
        assert np.mean(np.abs(empirical - model)) < 0.06
        assert abs(np.mean(fields.var(axis=0)) - 1.0) < 0.1

    def test_unit_variance_symmetric_positive_definite(self):
        idx = np.random.default_rng(3).choice(len(self.points), size=50, replace=False)
        corr = self.variogram.corr_matrix(self.points[idx], self.points[idx])
        np.testing.assert_allclose(np.diag(corr), 1.0, atol=1e-10)
        np.testing.assert_allclose(corr, corr.T, atol=1e-12)
        scipy.linalg.cholesky(corr + 1e-8 * np.eye(len(corr)))

    def test_correlates_across_bins(self):
        # Two points 25 degrees (2.5 bins) apart on a ring around the swirl centre.
        angles = np.radians([0.0, 25.0])
        locations = np.column_stack([200.0 + 150.0 * np.cos(angles), 150.0 + 150.0 * np.sin(angles)])
        independent = NonstationaryVariogram('matern52', 150.0, 40.0, azimuth=swirl_azimuth, n_bins=36)
        assert independent.corr_matrix(locations[:1], locations[1:])[0, 0] == 0.0
        assert self.variogram.corr_matrix(locations[:1], locations[1:])[0, 0] > 0.05

    def test_constant_azimuth_on_bin_matches_stationary(self):
        shared = NonstationaryVariogram(
            'matern52', 150.0, 40.0, azimuth=lambda p: np.full(len(p), 30.0), n_bins=36,
            shared_noise=True,
        )
        stationary = Variogram.from_parameters('matern52', 150.0, 40.0, azimuth=30.0)
        locations = self.points[[0, 820]]
        np.testing.assert_allclose(
            shared.corr_matrix(self.points, locations),
            stationary.corr_matrix(self.points, locations), atol=0.02,
        )

    def test_reproducible_and_distinct_realisations(self):
        grf.seed(9)
        first = SimpleKriging().simulate(self.grid, self.obs, self.variogram, n_sim=2)
        grf.seed(9)
        second = SimpleKriging().simulate(self.grid, self.obs, self.variogram, n_sim=2)
        np.testing.assert_array_equal(first[0], second[0])
        np.testing.assert_array_equal(first[1], second[1])
        assert not np.allclose(first[0], first[1])
        assert grf.seed() == 11
        # Realisation i uses the start seed + i.
        grf.seed(10)
        third = SimpleKriging().simulate(self.grid, self.obs, self.variogram)
        np.testing.assert_array_equal(third[0], first[1])

    @pytest.mark.parametrize('kriging', [SimpleKriging(), OrdinaryKriging()])
    def test_conditional_simulation_honours_observations(self, kriging):
        grf.seed(11)
        for sim in kriging.simulate(self.grid, self.obs, self.variogram, n_sim=2):
            for loc, value in zip(self.obs.locations, self.obs.values):
                assert abs(sim[tuple(np.rint(loc / 10.0).astype(int))] - value) < 1e-4

    def test_1d_locations_raise(self):
        with pytest.raises(NotImplementedError, match="2D or 3D"):
            self.variogram.corr_matrix(np.array([[0.0], [10.0]]), np.array([[0.0]]))


class TestSharedNoise3D:
    def setup_method(self):
        self.grid = GridSpec((24, 24, 4), (10.0, 10.0, 5.0))
        self.points = self.grid.coordinates()
        self.variogram = NonstationaryVariogram(
            'matern52', 100.0, 30.0, 15.0, azimuth=swirl_azimuth, dip=10.0, n_bins=18,
            shared_noise=True, lattice_size_3d=(128, 64),
        )

    def test_components_are_rotations_about_z(self):
        lags = np.random.default_rng(0).uniform(-100.0, 100.0, (20, 3))
        for k in [1, 5]:
            theta = np.radians(self.variogram.help_azimuths[k])
            cos, sin = np.cos(theta), np.sin(theta)
            rotated = np.column_stack(
                [cos * lags[:, 0] + sin * lags[:, 1], -sin * lags[:, 0] + cos * lags[:, 1], lags[:, 2]]
            )
            np.testing.assert_allclose(
                self.variogram.component(k).corr_array(lags),
                self.variogram.component(0).corr_array(rotated), atol=1e-12,
            )

    def test_constant_azimuth_on_bin_matches_stationary(self):
        shared = NonstationaryVariogram(
            'matern52', 100.0, 30.0, 15.0, azimuth=lambda p: np.full(len(p), 40.0), dip=10.0,
            n_bins=18, shared_noise=True, lattice_size_3d=(128, 64),
        )
        stationary = Variogram.from_parameters('matern52', 100.0, 30.0, 15.0, azimuth=40.0, dip=10.0)
        locations = self.points[[0, 1000, 2303]]
        np.testing.assert_allclose(
            shared.corr_matrix(self.points, locations),
            stationary.corr_matrix(self.points, locations), atol=0.05,
        )

    def test_layered_matches_empirical_covariance(self):
        nodes = [(12, 20, 0), (12, 20, 2), (3, 12, 3), (18, 18, 1)]
        idx = [np.ravel_multi_index(ijk, self.grid.shape) for ijk in nodes]
        model = self.variogram.corr_matrix(self.points, self.points[idx])
        grf.seed(1)
        n = 300
        fields = np.array([self.variogram.simulate(self.grid).ravel() for _ in range(n)])
        empirical = fields.T @ fields[:, idx] / n
        assert np.mean(np.abs(empirical - model)) < 0.06
        assert abs(np.mean(fields.var(axis=0)) - 1.0) < 0.1

    def test_single_layer_is_section_of_3d_field(self):
        grid = GridSpec((24, 24, 1), (10.0, 10.0, 5.0))
        points = grid.coordinates()
        idx = [np.ravel_multi_index(ijk, grid.shape) for ijk in [(12, 20, 0), (3, 12, 0)]]
        model = self.variogram.corr_matrix(points, points[idx])
        grf.seed(2)
        n = 300
        fields = np.array([self.variogram.simulate(grid).ravel() for _ in range(n)])
        assert fields.shape[1] == len(points)
        assert np.mean(np.abs(fields.T @ fields[:, idx] / n - model)) < 0.06

    def test_unit_variance_symmetric_positive_definite(self):
        idx = np.random.default_rng(3).choice(len(self.points), size=50, replace=False)
        corr = self.variogram.corr_matrix(self.points[idx], self.points[idx])
        np.testing.assert_allclose(np.diag(corr), 1.0, atol=1e-10)
        np.testing.assert_allclose(corr, corr.T, atol=1e-12)
        scipy.linalg.cholesky(corr + 1e-8 * np.eye(len(corr)))

    @pytest.mark.parametrize('kriging', [SimpleKriging(), OrdinaryKriging()])
    def test_conditional_simulation_honours_observations_in_layers(self, kriging):
        obs = ObservationData(
            np.array([[50.0, 50.0, 0.0], [150.0, 150.0, 10.0], [100.0, 200.0, 15.0]]),
            np.array([1.0, -1.0, 0.5]), np.zeros(3),
        )
        grf.seed(11)
        for sim in kriging.simulate(self.grid, obs, self.variogram, n_sim=2):
            for loc, value in zip(obs.locations, obs.values):
                assert abs(sim[tuple(np.rint(loc / self.grid.spacing).astype(int))] - value) < 1e-4
