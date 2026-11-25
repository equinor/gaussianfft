from __future__ import annotations
from collections.abc import Callable

from ._version import __version__
from enum import Enum
from importlib.util import find_spec
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from gaussianfft._kriging.api import KrigingType

if find_spec("numpy") is None:
    raise ImportError("gaussianfft requires NumPy to be installed")

import gaussianfft._platform  # noqa: F401  (sets up DLL paths before loading C extension)

from _gaussianfft import Variogram, advanced, quote, simulate, simulation_size
from _gaussianfft import variogram as _c_variogram

from ._rng import seed


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
    return _c_variogram(type, *args, **kwargs)


def nonstationary_variogram(
    type_: str,
    main_range: float,
    perp_range: float = -1.0,
    depth_range: float = -1.0,
    *,
    azimuth_callable: Callable[[np.ndarray], np.ndarray] | None = None,
    gridded_azimuth_values: np.ndarray | None = None,
    gridded_azimuth_spacing: tuple[float, ...] | None = None,
    dip: float = 0.0,
    power: float = 1.5,
):
    from gaussianfft._kriging.nonstationary_variogram import (
        create_nonstationary_variogram,
    )
    return create_nonstationary_variogram(
        type_, main_range, perp_range, depth_range,
        azimuth_callable=azimuth_callable,
        gridded_azimuth_values=gridded_azimuth_values,
        gridded_azimuth_spacing=gridded_azimuth_spacing,
        dip=dip,
        power=power,
    )


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
    if len(grid_shape) != len(grid_spacing):
        raise ValueError("grid_spacing must have the same length as grid_shape")
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
    if len(grid_shape) != len(grid_spacing):
        raise ValueError("grid_spacing must have the same length as grid_shape")
    from gaussianfft._kriging import predict as _kriging_predict
    return _kriging_predict(
        variogram, grid_shape, grid_spacing, obs_locations, obs_values, obs_uncertainties,
        mean=mean, method=method, calculate_stddev=calculate_stddev,
    )
