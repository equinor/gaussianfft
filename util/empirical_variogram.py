import random
from time import perf_counter

import gaussianfft
import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import binned_statistic

from gaussianfft.util.empirical_variogram2 import EmpiricalVariogram2


class EmpiricalVariogram:
    def __init__(self, v: gaussianfft.Variogram, nx, dx, ny, dy, nz, dz, px, py, pz):
        self.nx, self.ny, self.nz = nx, ny, nz
        self.dx, self.dy, self.dz = dx, dy, dz
        self.px, self.py, self.pz = px, py, pz
        self.v = v
        self.points, self.indexes = EmpiricalVariogram.find_grid_points(self.nx, self.dx,
                                                                        self.ny, self.dy,
                                                                        self.nz, self.dz)
        self.tuple_indexes = [tuple(i) for i in self.indexes]

    def estimate_variogram(self, nmax, resolution, reference_points, analyze_convergence=0):
        """
        Main function of this class. Used to estimate the variogram.

        :param nmax:                The number of simulations
        :param resolution:          Resolution of the output variogram
        :param reference_points:    List of length 3 tuples with each tuple representing a grid point from where the
                                    variogram is estimated.
        :param analyze_convergence: Sample deviation from the true variogram at an interval determined by this value.
                                    If <= 0, then this is ignored, which will reduce memory consumption.
        :return:
            [0] distance values, shape (N, )
            [1] estimated variogram at each distance value, shape (N, )
        """
        midpoints = self.find_midpoints(resolution)
        accumulated_sum = np.zeros_like(midpoints)
        n_samples = np.zeros_like(midpoints)
        tdata = {'sim': [], 'est': []}
        ca = ConvergenceAnalyzer(midpoints, self.true_variogram(resolution)[1])
        for i in range(nmax):
            t0 = perf_counter()
            s = self.simulate()
            t1 = perf_counter() - t0
            tdata['sim'].append(t1)
            t2 = perf_counter()
            # Find the mean for all reference points
            local_acc_mean = np.zeros_like(accumulated_sum)
            local_count = np.zeros_like(local_acc_mean)
            for ref in reference_points:
                means, _ = self.binned_variogram_statistics(resolution, s, ref)
                means = 1 - means / 2.0  # This will ensure an unbiased estimator for the variogram
                len_diff = len(accumulated_sum) - len(means)
                local_acc_mean += np.pad(means, (0, len_diff), 'constant')
                local_count += np.pad(np.ones_like(means), (0, len_diff), 'constant')
            # May divide on zero here, but that is okay. Interpreting nan as missing data will be the correct
            # interpretation
            local_acc_mean /= local_count
            # Add the means to the total accumulated
            accumulated_sum += local_acc_mean
            n_samples += local_count
            t3 = perf_counter() - t2
            tdata['est'].append(t3)
            if analyze_convergence > 0 and not i % analyze_convergence:
                ca.feed(accumulated_sum/(i+1))
        accumulated_mean = accumulated_sum / nmax
        return midpoints, accumulated_mean, n_samples, tdata, ca

    def true_variogram(self, resolution):
        """
        Useful for comparison with the true variogram
        :param resolution:
        :return:
        """
        midpoints = self.find_midpoints(resolution)
        true_variogram = []
        for m in midpoints:
            # This will only work for a variogram with equal ranges in each dimension. Should otherwise use
            # self.v.corr(m1, m2[, m3]) instead
            true_variogram.append(self.v.corr(m))
        return midpoints, np.array(true_variogram)

    def pick_reference_points(self, strategy, n=0, offset=0, seed=None):
        """
        Utility function for finding reference points based on a high level strategy instead of low level control
        of reference points.
        :param strategy: The strategy to use. See below for options
        :param n:        The (approximate) number of points. Valid for 'random' and 'regular' strategies
        :param offset:   First tupled index to use. Valid for 'regular' stategy
        :param seed:     Sets the random seed. Valid for 'random' strategy
        :return:
        """
        if seed is not None:
            random.seed(seed)
        if strategy == 'all':
            reference_points = self.tuple_indexes
        elif strategy == 'origo':
            reference_points = [(0, 0, 0)]
        elif strategy == 'center':
            reference_points = [(int(self.nx/2), int(self.ny/2), int(self.nz/2))]
        elif strategy == 'random':
            reference_points = random.sample(self.tuple_indexes, n)
        elif strategy == 'regular':
            reference_points = self.tuple_indexes[offset::int(len(self.tuple_indexes)/n)]
        else:
            raise ValueError("Invalid strategy '{}'".format(strategy))
        return reference_points

    """********************************************************"""
    """ Primarily utility functions used by estimate_variogram """
    """********************************************************"""

    def calculate_deltas(self, grid, ref=None):
        ref = ref or (0, 0, 0)
        if self.ny == 1:
            grid = grid.reshape((self.nx, 1, 1))
        elif self.nz == 1:
            grid = grid.reshape((self.nx, self.ny, 1))

        p_idx = self.tuple_indexes.index(ref)
        dists = cdist(self.points[p_idx].reshape((1, 3)), self.points)
        delta = grid - grid[ref]
        delta_flat = delta[self.indexes[:, 0], self.indexes[:, 1], self.indexes[:, 2]]

        return dists, delta_flat

    def binned_variogram_statistics(self, resolution, grid, ref=None):
        dists, deltas = self.calculate_deltas(grid, ref)
        dists = dists.flatten()
        deltas2 = np.square(deltas)
        nbins = int(np.max(dists)/resolution)
        mean_stats, edges, _ = binned_statistic(dists, deltas2, statistic='mean', bins=nbins)
        return mean_stats, edges

    def find_midpoints(self, resolution):
        s = self.simulate()
        means, edges = self.binned_variogram_statistics(resolution, s)
        return edges[:-1] + np.diff(edges)[0]

    def simulate(self):
        s = gaussianfft.advanced.simulate(self.v,
                                    self.nx, self.dx,
                                    self.ny, self.dy,
                                    self.nz, self.dz,
                                    padx=self.px, pady=self.py, padz=self.pz)
        s = np.array(s).reshape((self.nx, self.ny, self.nz), order='F')
        return s

    def dummy_sim(self):
        # Simulate dummy data with no variance, but exact variogram generation.
        # Can be used to verify that estimate_variogram works as intended, e.g.
        # by monkey patching the simulate function before estimation is done:
        #   e = EmpiricalVariogram(...)
        #   e.simulate = e.dummy_sim
        #   result = e.estimate_variogram(...)
        ref = (0, 0, 0)
        p_idx = self.tuple_indexes.index(ref)
        dists = cdist(self.points[p_idx].reshape((1, 3)), self.points)
        dists = dists.flatten()
        s_values = [np.sqrt((1-self.v.corr(d)) * 2) for d in dists]
        s = np.zeros((self.nx, self.ny, self.nz))
        s[self.indexes[:, 0], self.indexes[:, 1], self.indexes[:, 2]] = s_values
        return s

    @staticmethod
    def find_grid_points(nx, dx, ny=1, dy=0.0, nz=1, dz=0.0):
        points = []
        indexes = []
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    points.append([dx * i, dy * j, dz * k])
                    indexes.append((i, j, k))
        return np.array(points), np.array(indexes)


class ConvergenceAnalyzer:
    def __init__(self, midpoints, true_variogram):
        self.midpoints = midpoints
        self.true_variogram = true_variogram
        self._deltas = []

    def feed(self, est_variogram):
        self._deltas.append(est_variogram - self.true_variogram)

    @property
    def deltas(self):
        return np.array(self._deltas)
