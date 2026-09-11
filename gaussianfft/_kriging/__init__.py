from typing import Union

from numpy import ndarray

from gaussianfft._kriging.kriging_toolkit import SimpleKriging, OrdinaryKriging

__all__ = ['predict', 'simulate']

_METHODS = {
    'SimpleKriging': SimpleKriging,
    'OrdinaryKriging': OrdinaryKriging,
}


def _build_kriging(method, variogram, nx, dx, ny, dy, nz, dz,
                   obs_locations, obs_values, obs_uncertainties, mean):
    cls = _METHODS.get(method)
    if cls is None:
        raise ValueError(
            f"Unknown kriging method: {method!r}. Choose from {list(_METHODS)}"
        )
    if method == 'SimpleKriging':
        return cls(variogram, nx, dx, ny, dy, nz, dz,
                   obs_locations, obs_values, obs_uncertainties, mean=mean)
    elif method == 'OrdinaryKriging':
        return cls(variogram, nx, dx, ny, dy, nz, dz,
                   obs_locations, obs_values, obs_uncertainties)
    else:
        raise ValueError(f"Unsupported kriging method: {method!r}")

def _parse_grid_and_obs(args, kwargs):
    """Parse positional/keyword args: [ny, dy, [nz, dz,]] obs_locations, obs_values, obs_uncertainties."""
    ny = kwargs.pop('ny', None)
    dy = kwargs.pop('dy', None)
    nz = kwargs.pop('nz', None)
    dz = kwargs.pop('dz', None)
    if kwargs:
        unexpected = next(iter(kwargs))
        raise TypeError(f"unexpected keyword argument {unexpected!r}")

    if ny is not None:
        # Grid dims passed as keyword arguments; all positional args are obs
        if dy is None:
            raise TypeError("dy must be provided when ny is given")
        if nz is None:
            nz = 1
        if dz is None:
            dz = 1.0
        if len(args) != 3:
            raise TypeError(
                "When ny/dy/nz/dz are keyword arguments, exactly 3 positional args "
                "(obs_locations, obs_values, obs_uncertainties) are expected"
            )
        obs_locations, obs_values, obs_uncertainties = args
    else:
        if dy is not None or nz is not None or dz is not None:
            raise TypeError("ny must be provided when dy, nz, or dz are given as keyword arguments")
        # All positional
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
                "predict/simulate expects grid args followed by "
                "obs_locations, obs_values, obs_uncertainties. "
                "Valid patterns: (variogram, nx, dx, obs...), "
                "(variogram, nx, dx, ny, dy, obs...), "
                "(variogram, nx, dx, ny, dy, nz, dz, obs...)"
            )
    return ny, dy, nz, dz, obs_locations, obs_values, obs_uncertainties


def predict(variogram, nx, dx, *args, method='SimpleKriging', mean: Union[float, ndarray] = 0.0, **kwargs):
    ny, dy, nz, dz, obs_locations, obs_values, obs_uncertainties = _parse_grid_and_obs(args, kwargs)
    k = _build_kriging(method, variogram, nx, dx, ny, dy, nz, dz,
                       obs_locations, obs_values, obs_uncertainties, mean)
    return k.predict()


def simulate(variogram, nx, dx, *args, method='SimpleKriging', mean: Union[float, ndarray] = 0.0, n_sim=1, **kwargs):
    ny, dy, nz, dz, obs_locations, obs_values, obs_uncertainties = _parse_grid_and_obs(args, kwargs)
    k = _build_kriging(method, variogram, nx, dx, ny, dy, nz, dz,
                       obs_locations, obs_values, obs_uncertainties, mean)
    return k.simulate(n_sim=n_sim)