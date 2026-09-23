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
