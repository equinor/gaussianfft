import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import gaussianfft as grf


@pytest.fixture(scope='module')
def notebook():
    pytest.importorskip('marimo')
    pytest.importorskip('scipy')
    path = Path(__file__).resolve().parents[1] / 'notebooks' / 'interactive-3d-test.py'
    spec = importlib.util.spec_from_file_location('interactive_3d', path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('method', ['simple', 'ordinary'])
@pytest.mark.parametrize('twist', [0, 45])
@pytest.mark.parametrize('measurement_error', [0.0, 0.005])
@pytest.mark.parametrize(
    'kind', ['exponential', 'gaussian', 'spherical', 'general_exponential', 'matern32', 'matern52', 'matern72']
)
def test_conditional_panel_resampling(notebook, method, twist, measurement_error, kind):
    """Check conditional resampling, zero-noise observations, and slice interpolation."""
    locations = np.array([[200., 200., 200.], [600., 600., 600.], [400., 400., 400.]])
    observations = np.array([1.0, -1.0, 0.5])
    refs = {
        'grf': grf,
        'grid_shape': (9, 9, 9),
        'grid_spacing': (100.,) * 3,
        'kriging_method': SimpleNamespace(value=method),
        'mean_porosity': 0.22,
        'model_variogram': notebook.make_variogram(kind, 300, 100, 200, 45, twist),
        'normalized_observations': observations,
        'normalized_uncertainties': np.full(3, measurement_error / 0.04),
        'observation_locations': locations,
        'model_porosity_stddev': 0.04,
        'resample_conditional': SimpleNamespace(value=0),
    }
    _, first = notebook.simulate_conditional_field.run(**refs)
    _, repeated = notebook.simulate_conditional_field.run(**refs)
    refs['resample_conditional'] = SimpleNamespace(value=1)
    _, resampled = notebook.simulate_conditional_field.run(**refs)

    field = first['conditional_porosity']
    assert field.shape == (9, 9, 9)
    assert np.isfinite(field).all()
    np.testing.assert_array_equal(field, repeated['conditional_porosity'])
    assert not np.allclose(field, resampled['conditional_porosity'])
    np.testing.assert_array_equal(observations, [1.0, -1.0, 0.5])
    if measurement_error == 0:
        indices = tuple((locations / 100).astype(int).T)
        expected = 0.22 + 0.04 * observations
        np.testing.assert_allclose(field[indices], expected, atol=1e-8)
        np.testing.assert_allclose(resampled['conditional_porosity'][indices], expected, atol=1e-8)

@pytest.mark.parametrize('method', ['simple', 'ordinary'])
def test_assumed_noise_does_not_change_actual_observations(notebook, method):
    """Check assumed noise changes predictions without changing generated observations."""
    _, defs = notebook.app.run()
    _, noise_free = notebook.sample_wells.run(
        **{
            name: SimpleNamespace(value=0.0) if name == 'measurement_error' else defs[name]
            for name in notebook.sample_wells._cell.refs
            if name in defs
        }
    )
    expected_noise = np.random.default_rng(42 + defs['resample'].value).normal(
        0.0, defs['measurement_error'].value, defs['observed_porosity'].size
    )
    np.testing.assert_allclose(
        defs['observed_porosity'] - noise_free['observed_porosity'], expected_noise, atol=1e-16
    )
    np.testing.assert_array_equal(defs['reference_porosity'], noise_free['reference_porosity'])
    locations = defs['observation_locations'].copy()
    observations = defs['observed_porosity'].copy()
    results = []
    for assumed_noise in (0.0, 0.02):
        _, normalized = notebook.normalize_estimation_observations.run(
            observed_porosity=observations,
            mean_porosity=defs['mean_porosity'],
            model_porosity_stddev=0.06,
            model_measurement_error=assumed_noise,
            np=np,
        )
        refs = {
            **defs, **normalized, 'model_porosity_stddev': 0.06,
            'kriging_method': SimpleNamespace(value=method),
        }
        _, prediction = notebook.krige_well_data.run(
            **{name: refs[name] for name in notebook.krige_well_data._cell.refs}
        )
        results.append(prediction)
    assert not np.allclose(results[0]['estimated_porosity'], results[1]['estimated_porosity'])
    assert not np.allclose(results[0]['kriging_stddev'], results[1]['kriging_stddev'])
    np.testing.assert_array_equal(observations, defs['observed_porosity'])
    np.testing.assert_array_equal(locations, defs['observation_locations'])

