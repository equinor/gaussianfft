from ._version import __version__
from enum import Enum
from importlib.util import find_spec
from operator import index
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from gaussianfft._kriging.api import KrigingType

if find_spec("numpy") is None:
    raise ImportError("gaussianfft requires NumPy to be installed")

import gaussianfft._platform  # noqa: F401  (sets up DLL paths before loading C extension)

import _gaussianfft

from _gaussianfft import *

_set_c_seed = _gaussianfft.seed
_numpy_rng = np.random.RandomState()


def seed(value=None):
    """Seed GaussianFFT's private RNG. Integer seeds must be between 0 and 2**32 - 1.
    With no argument, return the C++ start seed without changing either RNG,
    unless NonstationaryVariogram.simulate() has been called with shared noise.
    The GaussianFFT streams are not isolated between threads or callers.
    """
    if value is None:
        return _set_c_seed()
    value = index(value)
    if not 0 <= value < 2**32:
        raise ValueError("Seed must be between 0 and 2**32 - 1")
    _set_c_seed(value)
    _numpy_rng.seed(value)


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


def conditional_simulate(
        variogram, grid_shape: tuple[int, ...], grid_spacing: tuple[float, ...],
        obs_locations, obs_values, obs_uncertainties, *,
        mean=0.0, n=1, method: 'KrigingType' = 'simple',
):
    """Generate conditional fields using shape and spacing tuples in x, y, z order."""
    from gaussianfft._kriging import simulate as _kriging_simulate
    return _kriging_simulate(
        variogram, grid_shape, grid_spacing, obs_locations, obs_values, obs_uncertainties,
        mean=mean, n_sim=n, method=method,
    )


def predict(
        variogram, grid_shape: tuple[int, ...], grid_spacing: tuple[float, ...],
        obs_locations, obs_values, obs_uncertainties, *,
        mean=0.0, method: 'KrigingType' = 'simple', calculate_stddev=False,
):
    """Predict a field using shape and spacing tuples in x, y, z order."""
    from gaussianfft._kriging import predict as _kriging_predict
    return _kriging_predict(
        variogram, grid_shape, grid_spacing, obs_locations, obs_values, obs_uncertainties,
        mean=mean, method=method, calculate_stddev=calculate_stddev,
    )
