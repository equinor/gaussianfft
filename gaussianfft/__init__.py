from ._version import __version__
from enum import Enum
from importlib.util import find_spec
if find_spec("numpy") is None:
    raise ImportError("gaussianfft requires NumPy to be installed")

try:
    # When using gaussianFFT in conjunction with Aspen RMS (former Emerson / Roxar)
    # you could experience a segmentation fault if gaussianfft was imported before
    # the roxar module.
    import roxar
except ImportError:
    pass

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
    '__version__',
]
