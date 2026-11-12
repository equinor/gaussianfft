from __future__ import annotations

from typing import Callable

import numpy as np
import scipy.interpolate
import scipy.ndimage

import gaussianfft
from gaussianfft._kriging.covariance import Covariance
from gaussianfft._kriging.grid_spec import GridSpec


class NonstationaryVariogram(Covariance):
    """Variogram with an azimuth that varies with location.

    The azimuth circle is discretized into ``n_bins`` help azimuths
    ``theta_m = m * 360 / n_bins``, each a stationary component ``C_m``.  A
    location with azimuth ``theta`` in ``[theta_a, theta_b)`` gets linear
    blending weights ``w_a ~ theta_b - theta`` and ``w_b ~ theta - theta_a``,
    normalized to unit variance.

    With independent component fields (the default), the correlation is
    ``sum_m w_m(s) w_m(s') C_m(s - s')``.  Locations whose azimuths are more than
    one bin apart are then uncorrelated, so the azimuth should vary slowly
    relative to the range and the bin width.

    With ``shared_noise=True`` all component fields are driven by the same white
    noise, and the correlation is ``sum_{m,n} w_m(s) w_n(s') C_mn(s - s')`` with
    cross-covariances ``C_mn`` = inverse Fourier transform of
    ``sqrt(S_m * S_n)``.  Correlation then extends across bins.  ``C_mn`` is
    tabulated on an internal lag lattice, with ``lattice_size`` nodes per axis
    for 2D locations and ``lattice_size_3d`` = (horizontal, vertical) nodes for
    3D locations.  3D grids are then always simulated with a 3D FFT, also with
    a single layer, so that the simulation matches the 3D tables.

    ``azimuth`` maps locations (n, ndim) to degrees, counter-clockwise from the
    first axis (the ``gaussianfft.variogram`` convention).  The other
    parameters are those of ``gaussianfft.variogram``.
    """

    def __init__(
        self, type, main_range: float, perp_range: float = -1.0, depth_range: float = -1.0, *,
        azimuth: Callable[[np.ndarray], np.ndarray], dip: float = 0.0, power: float = 1.5,
        n_bins: int = 100, shared_noise: bool = False, lattice_size: int = 512,
        lattice_size_3d: tuple[int, int] = (256, 64),
    ):
        if n_bins < 1:
            raise ValueError("n_bins must be a positive integer")
        self.azimuth = azimuth
        self.n_bins = int(n_bins)
        self.help_azimuths = np.arange(self.n_bins) * (360.0 / self.n_bins)
        self._shared_noise = bool(shared_noise)
        self._type = type
        self._variogram_args = dict(
            main_range=main_range, perp_range=perp_range, depth_range=depth_range, dip=dip, power=power,
        )
        self._ranges = tuple(r if r > 0 else main_range for r in (main_range, perp_range, depth_range))
        self._dip = np.radians(dip)
        horizontal, vertical = (int(n) for n in lattice_size_3d)
        self._lattice_sizes = {2: (int(lattice_size),) * 2, 3: (horizontal, horizontal, vertical)}
        self._components: dict[int, gaussianfft.Variogram] = {}
        self._tables = {}

    @property
    def shared_noise(self) -> bool:
        """Whether all component fields are driven by the same white noise."""
        return self._shared_noise

    def corr_matrix(self, points, locations) -> np.ndarray:
        points = np.asarray(points, dtype=float)
        locations = np.asarray(locations, dtype=float)
        if self._shared_noise:
            return self._shared_corr_matrix(points, locations)
        else:
            return self._non_shared_corr_matrix(points, locations)

    def _non_shared_corr_matrix(self, points, locations):
        """Independent-noise correlation ``sum_m w_m(s) w_m(s') C_m(s - s')``."""
        location_indices, location_weights = self.weights(locations)
        components = self._point_components(points)
        corr = np.zeros((len(points), len(locations)))
        for j, location in enumerate(locations):
            for m, location_weight in zip(location_indices[j], location_weights[j]):
                if location_weight == 0.0 or m not in components:
                    continue
                mask, component_points, point_weight = components[m]
                correlations = self.component(m).corr_array(component_points - location)
                correlations *= location_weight * point_weight
                if mask is None:
                    corr[:, j] += correlations
                else:
                    corr[mask, j] += correlations
        return corr

    def simulate(self, grid: GridSpec) -> np.ndarray:
        """Sum of stationary FFT fields, one per component, weighted per node.

        The component fields are independent, unless ``shared_noise`` is set.
        Then every component of a realisation is simulated with the same seed on
        the same padded FFT grid, so all components are driven by the same white
        noise, as assumed by ``corr_matrix``.  The realisation uses the last seed
        set and then sets the seed one higher for the next realisation.

        gaussianfft uses a 2D FFT for a single layer.  With shared noise, a
        single-layer 3D grid is simulated as two layers and the first is
        returned, so that the field is a section of a 3D field.
        """
        indices, weights = self.weights(grid.coordinates())
        components = np.unique(indices[weights > 0.0])
        shared = self._shared_noise and len(components) > 1
        sim_shape = tuple(grid.shape)
        if shared and len(sim_shape) == 3 and sim_shape[2] == 1:
            sim_shape = sim_shape[:2] + (2,)
        grid_args = tuple(value for axis in zip(sim_shape, grid.spacing) for value in axis)
        if shared:
            seed = gaussianfft.seed()
            sizes = [gaussianfft.simulation_size(self.component(m), *grid_args) for m in components]
            padding = np.max(sizes, axis=0) - np.asarray(sim_shape[:len(sizes[0])])
            pad_args = dict(zip(('padx', 'pady', 'padz'), (int(p) for p in padding)))
        field = np.zeros(grid.shape)
        for m in components:
            node_weights = np.sum(np.where(indices == m, weights, 0.0), axis=1).reshape(grid.shape)
            if shared:
                gaussianfft.seed(seed)
                raw = gaussianfft.advanced.simulate(self.component(m), *grid_args, **pad_args)
            else:
                raw = gaussianfft.simulate(self.component(m), *grid_args)
            raw = np.asarray(raw).reshape(sim_shape, order='F')
            field += node_weights * raw[tuple(slice(0, n) for n in grid.shape)]
        if shared:
            gaussianfft.seed(seed + 1)
        return field

    def _point_components(self, points):
        """Per component: point mask (None if all points), masked points and weights.

        Computed once per call so the loop over locations only evaluates
        ``corr_array`` on the points belonging to each component.
        """
        point_indices, point_weights = self.weights(points)
        components = {}
        for m in np.unique(point_indices[point_weights > 0.0]):
            weight = np.sum(np.where(point_indices == m, point_weights, 0.0), axis=1)
            mask = weight > 0.0
            if np.all(mask):
                components[m] = (None, points, weight)
            else:
                components[m] = (mask, points[mask], weight[mask])
        return components

    def _shared_corr_matrix(self, points, locations):
        """Shared-noise correlation ``sum_{m,n} w_m(s) w_n(s') C_mn(s - s')``.

        Components are rotations of component 0, so ``C_mn(h) = T_k(R(-theta_b) h)``
        where ``b`` is the base of the unordered pair {m, n} (the one from which
        the other is ``k = 0..n_bins/2`` bins ahead).  ``T_k`` is even, so the
        sign of ``h`` does not matter.  The base depends only on the pair, which
        makes the result exactly symmetric in points and locations.  The
        rotation is about the z axis, so a vertical lag is not rotated.
        """
        ndim = points.shape[1]
        tables, spacing, centre = self._cross_tables(ndim)
        n_bins = self.n_bins
        point_indices, point_weights = self.weights(points)
        location_indices, location_weights = self.weights(locations)
        corr = np.zeros((len(points), len(locations)))
        for j, location in enumerate(locations):
            lag = points - location
            z = [lag[:, 2] / spacing[2] + centre[2]] if ndim == 3 else []
            for m, location_weight in zip(location_indices[j], location_weights[j]):
                if location_weight == 0.0:
                    continue
                for slot in range(point_indices.shape[1]):
                    n = point_indices[:, slot]
                    ahead = (n - m) % n_bins
                    use_n = (ahead > n_bins - ahead) | ((ahead == n_bins - ahead) & (n < m))
                    k = np.where(use_n, n_bins - ahead, ahead)
                    theta = np.radians(self.help_azimuths[np.where(use_n, n, m)])
                    cos, sin = np.cos(theta), np.sin(theta)
                    x = (cos * lag[:, 0] + sin * lag[:, 1]) / spacing[0] + centre[0]
                    y = (-sin * lag[:, 0] + cos * lag[:, 1]) / spacing[1] + centre[1]
                    values = scipy.ndimage.map_coordinates(
                        tables, [k, x, y] + z, output=np.float64, order=1, cval=0.0,
                    )
                    corr[:, j] += location_weight * point_weights[:, slot] * values
        return corr

    def _cross_tables(self, ndim):
        """Tables ``T_k`` = IFFT(sqrt(S_0 S_k)), ``k = 0..n_bins/2``, on a lag lattice.

        The lattice covers 2D lags for ``ndim == 2`` and 3D lags for ``ndim == 3``.
        Returns (tables, spacing, centre) with per-axis spacing and lag 0 at
        index ``centre``.
        """
        if ndim not in (2, 3):
            raise NotImplementedError("shared_noise requires 2D or 3D locations")
        if ndim not in self._tables:
            sizes = self._lattice_sizes[ndim]
            main, sub, depth = self._ranges
            half_extent = 4.0 * max(main, sub, depth * abs(np.sin(self._dip)))
            spacing = [max(min(main, sub) / 8.0, 2.0 * half_extent / sizes[0])] * 2
            if ndim == 3:
                sin, cos = abs(np.sin(self._dip)), np.cos(self._dip)
                half_depth = 4.0 * np.hypot(main * sin, depth * cos)
                vertical_range = 1.0 / np.hypot(sin / main, cos / depth)
                spacing.append(max(vertical_range / 8.0, 2.0 * half_depth / sizes[2]))
            offsets = [np.fft.fftfreq(n) * n * d for n, d in zip(sizes, spacing)]
            lags = np.column_stack([lag.ravel() for lag in np.meshgrid(*offsets, indexing='ij')])
            tables = np.empty((self.n_bins // 2 + 1,) + sizes, dtype=np.float32)
            spectrum_0 = None
            for k in range(len(tables)):
                cov = self.component(k).corr_array(lags).reshape(sizes)
                spectrum = np.maximum(np.fft.rfftn(cov).real, 0.0)
                if spectrum_0 is None:
                    spectrum_0 = spectrum
                tables[k] = np.fft.irfftn(np.sqrt(spectrum_0 * spectrum), s=sizes, axes=range(ndim))
            tables /= tables[(0,) * (ndim + 1)]
            axes = tuple(range(1, ndim + 1))
            centre = tuple(n // 2 for n in sizes)
            self._tables[ndim] = (np.fft.fftshift(tables, axes=axes), tuple(spacing), centre)
        return self._tables[ndim]

    def component(self, m: int) -> gaussianfft.Variogram:
        """Stationary variogram of component ``m``, with azimuth ``help_azimuths[m]``."""
        if m not in self._components:
            self._components[m] = gaussianfft.variogram(
                self._type, azimuth=float(self.help_azimuths[m]), **self._variogram_args,
            )
        return self._components[m]

    def weights(self, locations) -> tuple[np.ndarray, np.ndarray]:
        """Component indices (n, 2) and blending weights (n, 2) at locations (n, ndim)."""
        azimuth = np.asarray(self.azimuth(np.asarray(locations, dtype=float)), dtype=float)
        if azimuth.shape != (len(locations),) or not np.all(np.isfinite(azimuth)):
            raise ValueError("azimuth must return one finite value per location")
        position = np.mod(azimuth, 360.0) / (360.0 / self.n_bins)
        idx_a = np.floor(position).astype(int) % self.n_bins
        idx_b = (idx_a + 1) % self.n_bins
        w_b = position - np.floor(position)
        w_a = 1.0 - w_b
        if self._shared_noise:
            # Adjacent component fields at the same location have correlation rho = T_1(0).
            tables, _, centre = self._cross_tables(np.shape(locations)[1])
            rho = float(tables[(min(1, len(tables) - 1),) + centre])
            norm = np.sqrt(w_a ** 2 + w_b ** 2 + 2.0 * w_a * w_b * rho)
        else:
            norm = np.sqrt(w_a ** 2 + w_b ** 2)
        return np.stack([idx_a, idx_b], axis=1), np.stack([w_a / norm, w_b / norm], axis=1)


class GriddedAzimuth:
    """Azimuth function interpolated bilinearly from values given at grid nodes.

    Interpolation is done on unit vectors, so it handles the wrap at 360 degrees.
    Locations outside the grid get the value at the nearest edge.  For 3D
    locations, 2D (nx, ny) values are used for every z.
    """

    def __init__(self, values, grid: GridSpec):
        values = np.asarray(values, dtype=float)
        n_axes = values.ndim
        if values.shape != grid.shape[:n_axes] or not np.all(np.isfinite(values)):
            raise ValueError(f"values must be finite with the grid shape {grid.shape}")
        axes = [
            origin + np.arange(size) * spacing
            for size, spacing, origin in zip(grid.shape[:n_axes], grid.spacing, grid.origin)
        ]
        radians = np.radians(values)
        self._lower = np.array([axis[0] for axis in axes])
        self._upper = np.array([axis[-1] for axis in axes])
        self._interpolator = scipy.interpolate.RegularGridInterpolator(
            axes, np.stack([np.cos(radians), np.sin(radians)], axis=-1),
        )

    def __call__(self, locations) -> np.ndarray:
        locations = np.asarray(locations, dtype=float)[:, :len(self._lower)]
        unit = self._interpolator(np.clip(locations, self._lower, self._upper))
        return np.mod(np.degrees(np.arctan2(unit[:, 1], unit[:, 0])), 360.0)
