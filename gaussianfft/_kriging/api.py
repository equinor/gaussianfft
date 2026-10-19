from typing import Literal

from gaussianfft._kriging.grid_spec import GridSpec
from gaussianfft._kriging.kriging_toolkit import OrdinaryKriging, SimpleKriging
from gaussianfft._kriging.observation_data import ObservationData


KrigingType = Literal["simple", "ordinary"]


def _build_kriging(method: KrigingType, mean: float):
    if method == 'simple':
        estimator = SimpleKriging(mean=mean)
    elif method == 'ordinary':
        estimator = OrdinaryKriging()
    else:
        raise ValueError(
            f"Unknown kriging method: {method!r}. Choose from 'simple' or 'ordinary'"
        )
    return estimator


def predict(
        variogram, grid_shape: tuple[int, ...], grid_spacing: tuple[float, ...],
        obs_locations, obs_values, obs_uncertainties, *,
        method: KrigingType = 'simple', mean: float = 0.0, calculate_stddev=False,
):
    """Predict on a grid defined by shape and spacing tuples in x, y, z order."""
    grid = GridSpec(grid_shape, grid_spacing)
    obs = ObservationData(obs_locations, obs_values, obs_uncertainties)
    estimator = _build_kriging(method, mean)
    return estimator.predict(grid, obs, variogram, calculate_stddev=calculate_stddev)


def simulate(
        variogram, grid_shape: tuple[int, ...], grid_spacing: tuple[float, ...],
        obs_locations, obs_values, obs_uncertainties, *,
        method: KrigingType = 'simple', mean: float = 0.0, n_sim=1,
):
    """Simulate on a grid defined by shape and spacing tuples in x, y, z order."""
    grid = GridSpec(grid_shape, grid_spacing)
    obs = ObservationData(obs_locations, obs_values, obs_uncertainties)
    estimator = _build_kriging(method, mean)
    return estimator.simulate(grid, obs, variogram, n_sim=n_sim)
