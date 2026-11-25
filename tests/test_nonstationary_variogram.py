import platform

import numpy as np
import pytest

if platform.python_implementation() == 'PyPy':
    pytest.skip('Kriging requires SciPy, which is unavailable on PyPy', allow_module_level=True)

import gaussianfft as grf


def swirl_azimuth(locations):
    angle = np.degrees(np.arctan2(locations[:, 1] - 150.0, locations[:, 0] - 200.0))
    return (angle + 90.0) % 360.0


def test_nonstationary_unconditional_simulation():
    model = grf.nonstationary_variogram('exponential', 10.0, azimuth_callable=swirl_azimuth)

    grf.seed(42)
    field = model.simulate(grid_shape=(40, 30), grid_spacing=(2.0, 5.0))

    assert field.shape == (40, 30)
    assert np.all(np.isfinite(field))


@pytest.mark.parametrize('shared_noise', [False, True])
def test_constant_azimuth_matches_stationary_prediction(shared_noise):
    model = grf.nonstationary_variogram(
        'matern52', 200.0, 50.0, azimuth_callable=lambda p: np.full(len(p), 36.0),
        n_bins=20, shared_noise=shared_noise,
    )
    stationary = grf.variogram('matern52', 200.0, 50.0, azimuth=36.0)
    args = ((40, 30), (10.0, 10.0), [[5.0, 5.0], [175.0, 75.0]], [1.0, -0.5], [0.0, 0.0])

    actual, _ = grf.predict(model, *args)
    expected, _ = grf.predict(stationary, *args)

    np.testing.assert_allclose(actual, expected, atol=0.02 if shared_noise else 1e-10)


def test_predict_rejects_nonfinite_azimuth():
    model = grf.nonstationary_variogram(
        'exponential', 100.0, azimuth_callable=lambda p: np.full(len(p), np.nan),
    )
    with pytest.raises(ValueError, match='finite'):
        grf.predict(model, (2, 2), (10.0, 10.0), [[5.0, 5.0]], [1.0], [0.0])


def test_gridded_azimuth_interpolates_across_wrap():
    shape, spacing = (2, 2), (10.0, 10.0)
    gridded = grf.nonstationary_variogram(
        'exponential', 100.0, 30.0,
        gridded_azimuth_values=np.array([[359.0, 359.0], [1.0, 1.0]]),
        gridded_azimuth_spacing=spacing,
    )
    # Prediction evaluates azimuth at x=5 and x=15 on the grid, and at the observation halfway between.
    reference = grf.nonstationary_variogram(
        'exponential', 100.0, 30.0, azimuth_callable=lambda p: (p[:, 0] - 10.0) / 5.0,
    )
    args = (shape, spacing, [[10.0, 5.0]], [1.0], [0.0])

    actual, _ = grf.predict(gridded, *args)
    expected, _ = grf.predict(reference, *args)

    np.testing.assert_allclose(actual, expected, atol=1e-10)


@pytest.mark.parametrize('method', ['simple', 'ordinary'])
@pytest.mark.parametrize('shared_noise', [False, True])
def test_nonstationary_kriging_honours_observations_in_layers(method, shared_noise):
    shape, spacing = (24, 24, 4), (10.0, 10.0, 5.0)
    model = grf.nonstationary_variogram(
        'matern52', 100.0, 30.0, 15.0, azimuth_callable=swirl_azimuth, dip=10.0,
        n_bins=8, shared_noise=shared_noise,
    )
    indices = np.array([(5, 5, 0), (15, 15, 2), (10, 20, 3)])
    locations = (indices + 0.5) * spacing
    values = [1.0, -1.0, 0.5]
    args = (model, shape, spacing, locations, values, np.zeros(len(values)))

    prediction, _ = grf.predict(*args, method=method)
    grf.seed(11)
    simulations = grf.conditional_simulate(*args, method=method, n=2)

    assert len(simulations) == 2
    np.testing.assert_allclose(prediction[tuple(indices.T)], values, atol=1e-6)
    for field in simulations:
        assert field.shape == shape
        np.testing.assert_allclose(field[tuple(indices.T)], values, atol=1e-4)


@pytest.mark.parametrize(('shape', 'spacing', 'nodes'), [
    ((40, 40), (10.0, 10.0), [(20, 35), (5, 20), (30, 30)]),
    ((24, 24, 4), (10.0, 10.0, 5.0), [(12, 20, 0), (12, 20, 2), (3, 12, 3)]),
], ids=['2d', '3d'])
def test_shared_noise_prediction_matches_simulated_covariance(shape, spacing, nodes):
    model = grf.nonstationary_variogram(
        'matern52', 100.0, 30.0, 15.0, azimuth_callable=swirl_azimuth, dip=10.0,
        n_bins=8, shared_noise=True,
    )
    indices = np.ravel_multi_index(np.array(nodes).T, shape)
    predicted_covariances = []
    for location in (np.array(nodes) + 0.5) * spacing:
        # With one exact unit observation and unit marginal variance, the simple kriging mean is the covariance.
        prediction, _ = grf.predict(model, shape, spacing, [location], [1.0], [0.0])
        predicted_covariances.append(prediction.ravel())

    grf.seed(1)
    n = 300
    fields = np.array([model.simulate(shape, spacing).ravel() for _ in range(n)])
    empirical_covariances = fields.T @ fields[:, indices] / n

    assert np.mean(np.abs(empirical_covariances - np.column_stack(predicted_covariances))) < 0.06
    assert np.mean(fields.var(axis=0)) == pytest.approx(1.0, abs=0.1)


def test_shared_noise_correlates_across_azimuth_bins():
    args = ((5, 2), (10.0, 10.0), [[5.0, 5.0]], [1.0], [0.0])
    predictions = []
    for shared_noise in (False, True):
        model = grf.nonstationary_variogram(
            'matern52', 150.0, 40.0, azimuth_callable=lambda p: np.where(p[:, 0] < 20.0, 0.0, 25.0),
            n_bins=36, shared_noise=shared_noise,
        )
        prediction, _ = grf.predict(model, *args)
        predictions.append(prediction[4, 0])

    independent, shared = predictions
    assert independent == 0.0
    assert shared > 0.05


def test_shared_noise_simulations_are_reproducible_and_distinct():
    model = grf.nonstationary_variogram(
        'matern52', 150.0, 40.0, azimuth_callable=swirl_azimuth, n_bins=8, shared_noise=True,
    )
    args = (model, (40, 40), (10.0, 10.0), [[105.0, 105.0], [305.0, 305.0]], [1.0, -1.0], [0.0, 0.0])

    grf.seed(9)
    batch = grf.conditional_simulate(*args, n=2)
    grf.seed(9)
    first, = grf.conditional_simulate(*args)
    second, = grf.conditional_simulate(*args)

    np.testing.assert_array_equal(batch, [first, second])
    assert not np.allclose(first, second)


def test_shared_noise_simulation_preserves_numpy_random_stream():
    model = grf.nonstationary_variogram(
        'matern52', 150.0, 40.0, azimuth_callable=swirl_azimuth, n_bins=8, shared_noise=True,
    )
    state = np.random.get_state()
    try:
        expected = np.random.RandomState(123).normal(size=8)
        np.random.seed(123)
        grf.seed(9)
        model.simulate((40, 40), (10.0, 10.0))

        np.testing.assert_array_equal(np.random.normal(size=8), expected)
    finally:
        np.random.set_state(state)


def test_shared_noise_rejects_1d_prediction():
    model = grf.nonstationary_variogram(
        'matern52', 150.0, 40.0, azimuth_callable=lambda p: np.zeros(len(p)), shared_noise=True,
    )
    with pytest.raises(NotImplementedError, match='2D or 3D'):
        grf.predict(model, (2,), (10.0,), [[5.0]], [1.0], [0.0])
