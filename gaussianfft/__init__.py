from ._version import __version__
from enum import Enum
from importlib.util import find_spec
if find_spec("numpy") is None:
    raise ImportError("gaussianfft requires NumPy to be installed")

import gaussianfft._platform  # noqa: F401  (sets up DLL paths before loading C extension)

import _gaussianfft

from _gaussianfft import *


class VariogramType(Enum):
    GAUSSIAN = 'gaussian'
    EXPONENTIAL = 'exponential'
    GENERAL_EXPONENTIAL = 'general_exponential'
    SPHERICAL = 'spherical'
    MATERN_32 = 'matern32'
    MATERN_52 = 'matern52'
    MATERN_72 = 'matern72'
    CONSTANT = 'constant'


def variogram(type, *args, **kwargs):
    if isinstance(type, Enum):
        type = type.value
    return _gaussianfft.variogram(type, *args, **kwargs)


__all__ = [
    'variogram', 'simulate', 'seed', 'advanced', 'simulation_size',
    'quote', 'Variogram', 'VariogramType', 'util', 'SizeTVector', 'DoubleVector',
    'conditional_simulate', 'predict',
    '__version__',
]


def _parse_grid_and_obs(args):
    """Parse positional args: [ny, dy, [nz, dz,]] obs_locations, obs_values, obs_uncertainties."""
    # Last 3 args are always obs_locations, obs_values, obs_uncertainties
    if len(args) == 3:
        ny, dy, nz, dz = 1, 1.0, 1, 1.0
        obs_locations, obs_values, obs_uncertainties = args
    elif len(args) == 5:
        ny, dy = args[0], args[1]
        nz, dz = 1, 1.0
        obs_locations, obs_values, obs_uncertainties = args[2], args[3], args[4]
    elif len(args) == 7:
        ny, dy, nz, dz = args[0], args[1], args[2], args[3]
        obs_locations, obs_values, obs_uncertainties = args[4], args[5], args[6]
    else:
        raise TypeError(
            "conditional_simulate/predict expects grid args followed by "
            "obs_locations, obs_values, obs_uncertainties. "
            "Valid patterns: (variogram, nx, dx, obs...), "
            "(variogram, nx, dx, ny, dy, obs...), "
            "(variogram, nx, dx, ny, dy, nz, dz, obs...)"
        )
    return ny, dy, nz, dz, obs_locations, obs_values, obs_uncertainties


def conditional_simulate(variogram, nx, dx, *args, mean=0.0, n=1, seed=None, method='SimpleKriging', **kwargs):
    if seed is not None:
        _gaussianfft.seed(seed)
    from gaussianfft._kriging import simulate as _kriging_simulate
    return _kriging_simulate(
        variogram, nx, dx, *args, mean=mean, n_sim=n, method=method, **kwargs,
    )


def predict(variogram, nx, dx, *args, mean=0.0, method='SimpleKriging', **kwargs):
    from gaussianfft._kriging import predict as _kriging_predict
    return _kriging_predict(
        variogram, nx, dx, *args, mean=mean, method=method, **kwargs,
    )
