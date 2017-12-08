import random
from time import perf_counter

import numpy as np
import nrlib
from scipy.spatial.distance import cdist, pdist, squareform
from scipy.stats import binned_statistic
from scipy.sparse.csgraph import connected_components


class EmpiricalVariogram2:
    reference_point = (0, 0, 0)

    """
    Alternative way of estimating the variogram
    """
    def __init__(self, v: nrlib.Variogram, nx, ny, nz, px, py, pz, close_range, step):
        self.nx, self.ny, self.nz = nx, ny, nz
        self.dx, self.dy, self.dz = 1.0, 1.0, 1.0
        self.px, self.py, self.pz = px, py, pz
        self.v = v
        self.points, self.indexes = EmpiricalVariogram.find_grid_points(self.nx, self.dx,
                                                                        self.ny, self.dy,
                                                                        self.nz, self.dz)
        self.tuple_indexes = [tuple(i) for i in self.indexes]
        self.dists_from_ref = self._calculate_dists()

        # Indexes to close points, used for estimating the variogram for the short range
        self.ix_short_points = self.dists_from_ref < close_range

        # Indexes for sample points
        self.ix_sample_points = np.array([
            all((j % step == 0) for j in i)
            for i in self.tuple_indexes
        ], dtype=np.bool)

        self.short_bins = self._find_distance_bins(self.ix_short_points)
        self.sample_bins = self._find_distance_bins(self.ix_sample_points)

        # For validation
        self.s = None

    """ Initialization """
    def _calculate_dists(self):
        p_idx = self.tuple_indexes.index(EmpiricalVariogram2.reference_point)
        dists = cdist(self.points[p_idx].reshape((1, 3)), self.points)
        return dists.flatten()

    def _find_distance_bins(self, indexes):
        dists = self.dists_from_ref[indexes]
        pairwise_dists = squareform(pdist(dists.reshape((-1, 1))))
        closeness = pairwise_dists < 1e-10
        n_comps, labels = connected_components(closeness, False)
        groups = [
            np.argwhere(labels == i).flatten()
            for i in range(n_comps)
        ]
        group_dists = [dists[g[0]] for g in groups]
        return n_comps, groups, group_dists

    """ Estimation"""
    def _simulate(self):
        s = nrlib.advanced.simulate(self.v,
                                    self.nx, self.dx,
                                    self.ny, self.dy,
                                    self.nz, self.dz,
                                    padx=self.px, pady=self.py, padz=self.pz)
        self.s = np.array(s).reshape((self.nx, self.ny, self.nz), order='F')
        return self.s

    def _estimate_variogram_data(self, nmax):
        short_bin_data = np.zeros((nmax, self.short_bins[0]))
        sample_bin_data = np.zeros((nmax, self.sample_bins[0]))
        for i in range(nmax):
            s = self._simulate()
            d = np.square(self._calculate_all_deltas(s))

            short_d = d[self.ix_short_points]
            sample_d = d[self.ix_sample_points]

            for j, c in enumerate(self.short_bins[1]):
                short_bin_data[i, j] = np.mean(short_d[c])

            for j, c in enumerate(self.sample_bins[1]):
                sample_bin_data[i, j] = np.mean(sample_d[c])

        return short_bin_data, sample_bin_data

    def estimate_variogram(self, nmax):
        vdata_short, vdata_sample = self._estimate_variogram_data(nmax)
        x_short = self.short_bins[2]
        x_sample = self.sample_bins[2]
        y_short = np.mean(vdata_short, axis=0)
        y_sample = np.mean(vdata_sample, axis=0)
        y_err_short = np.std(vdata_short, axis=0)
        y_err_sample = np.std(vdata_sample, axis=0)
        return (x_short, y_short, y_err_short), (x_sample, y_sample, y_err_sample)

    def _calculate_all_deltas(self, grid):
        if self.ny == 1:
            grid = grid.reshape((self.nx, 1, 1))
        elif self.nz == 1:
            grid = grid.reshape((self.nx, self.ny, 1))

        delta = grid - grid[EmpiricalVariogram2.reference_point]
        delta_flat = delta[self.indexes[:, 0], self.indexes[:, 1], self.indexes[:, 2]]
        return delta_flat


class EmpiricalVariogram:
    def __init__(self, v: nrlib.Variogram, nx, dx, ny, dy, nz, dz, px, py, pz):
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
        s = nrlib.advanced.simulate(self.v,
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


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    # Next steps:
    # - structured testing of the parameters. Verify the hypothesis that 4x range is sufficient
    # - 1D verification that the estimation is working as intended.
    nx, ny, nz = 50, 50, 1
    r = 70
    px, py, pz = int(nx/1), int(ny/1), int(nz)
    v = nrlib.variogram('spherical', r, r, r)
    ev = EmpiricalVariogram2(v, nx, ny, nz, px, py, pz, 30.0, 10)
    (x_short, y_short, y_err_short), (x_sample, y_sample, y_err_sample) = ev.estimate_variogram(1000)

    plt.subplot(121)
    plt.title('n+p={}, range={}'.format(nx + px, r))
    plt.plot(x_short, 0.5 * y_short, 'o')
    plt.plot(x_sample, 0.5 * y_sample, 'o')

    x_true = np.linspace(0, np.sqrt(nx ** 2 + ny ** 2 + nz ** 2), 100)
    y_true = [1.0 - v.corr(x) for x in x_true]
    plt.plot(x_true, y_true)

    plt.subplot(122)
    plt.imshow(ev.s[:, :, int(ev.s.shape[2]/2)], interpolation='None')

    plt.show()
