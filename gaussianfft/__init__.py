from enum import Enum
from importlib.util import find_spec

from ._version import __version__

if find_spec('numpy') is None:
    raise ImportError('gaussianfft requires NumPy to be installed')


import _gaussianfft
from _gaussianfft import (
    Variogram,
    quote,
    seed,
    simulate,
    simulation_size,
)


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
    'variogram',
    'simulate',
    'seed',
    'simulation_size',
    'quote',
    'Variogram',
    'VariogramType',
    '__version__',
]
