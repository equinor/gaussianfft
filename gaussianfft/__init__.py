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

_seed = _gaussianfft.seed


def seed(value=None):
    """Seed both the field generator and NumPy's global RNG.

    Integer seeds must be between 0 and 2**32 - 1. This also resets randomness
    used by other callers of numpy.random, but not separate Generator instances.
    With no argument, return the C++ start seed without changing either RNG.
    The two global streams are not isolated between threads or callers.
    """
    if value is None:
        return _seed()
    value = index(value)
    if not 0 <= value < 2**32:
        raise ValueError("Seed must be between 0 and 2**32 - 1")
    _seed(value)
    np.random.seed(value)


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
        mean=0.0, n=1, seed=None, method: 'KrigingType' = 'simple',
):
    """Generate conditional fields using shape and spacing tuples in x, y, z order.
    An explicit seed resets both global RNGs, just like gaussianfft.seed()."""
    if seed is not None:
        from gaussianfft import seed as set_seed
        set_seed(seed)
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
