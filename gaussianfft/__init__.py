from enum import Enum

try:
    # When using gaussianFFT in conjunction with Aspen RMS (former Emerson / Roxar)
    # you could experience a segmentation fault if gaussianfft was imported before
    # the roxar module.
    import roxar
except ImportError:
    pass

import _gaussianfft

from _gaussianfft import *


__version__ = "1.1.1b1"


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
    '__version__',
]
