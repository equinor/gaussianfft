import gaussianfft
import numpy as np
from scipy.sparse.csgraph._traversal import connected_components
from scipy.spatial.distance import cdist, squareform, pdist


class EmpiricalVariogram2:
    reference_point = (0, 0, 0)
    smoothing = 0.00001

    """
    Estimates the variogram, given the provided parameters.
    """
    def __init__(self, v: gaussianfft.Variogram, nx, ny, nz, px, py, pz, close_range, step):
        """
        Creates a variogram estimation class.

        :param v:   A gaussianfft.Variogram instance
        :param nx:  Number of grid cells in x-direction
        :param ny:                          y-direction
        :param nz:                          z-direction
        :param px:  Number of cells to pad with in x-direction
        :param py:                                 y-direction
        :param pz:                                 z-direction
        :param close_range:  Float value defining the range that is considered 'close'. All points within this range are
                             included in the estimation
        :param step:  Sampling resolution in number of cells when beyond close range.
        """
        self.nx, self.ny, self.nz = nx, ny, nz
        self.dx, self.dy, self.dz = 1.0, 1.0, 1.0
        self.px, self.py, self.pz = px, py, pz
        self.v = v
        self.points, self.indexes = EmpiricalVariogram2.find_grid_points(self.nx, self.dx,
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
        ], dtype=bool)

        self.short_bins = self._find_distance_bins(self.ix_short_points)
        self.sample_bins = self._find_distance_bins(self.ix_sample_points)

        # For validation
        self.s = None

    """ External function """
    def estimate_variogram(self, nmax):
        vdata_short, vdata_sample = self._estimate_variogram_data(nmax)
        x_short = self.short_bins[2]
        x_sample = self.sample_bins[2]
        y_short = np.mean(vdata_short, axis=0)
        y_sample = np.mean(vdata_sample, axis=0)
        y_err_short = np.std(vdata_short, axis=0)
        y_err_sample = np.std(vdata_sample, axis=0)
        return (x_short, y_short, y_err_short), (x_sample, y_sample, y_err_sample)

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

    """ Estimation, internal functions """
    def _simulate(self):
        s = gaussianfft.advanced.simulate(self.v,
                                    self.nx, self.dx,
                                    self.ny, self.dy,
                                    self.nz, self.dz,
                                    padx=self.px, pady=self.py, padz=self.pz,
                                    sx=EmpiricalVariogram2.smoothing,
                                    sy=EmpiricalVariogram2.smoothing,
                                    sz=EmpiricalVariogram2.smoothing)
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

    def _calculate_all_deltas(self, grid):
        if self.ny == 1:
            grid = grid.reshape((self.nx, 1, 1))
        elif self.nz == 1:
            grid = grid.reshape((self.nx, self.ny, 1))

        delta = grid - grid[EmpiricalVariogram2.reference_point]
        delta_flat = delta[self.indexes[:, 0], self.indexes[:, 1], self.indexes[:, 2]]
        return delta_flat

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


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    # Next steps:
    # - structured testing of the parameters. Verify the hypothesis that 4x range is sufficient
    # - 1D verification that the estimation is working as intended.
    nx, ny, nz = 100, 100, 1
    r = 600
    px, py, pz = 300, 300, 0
    v = gaussianfft.variogram('exponential', r, r, r)
    ev = EmpiricalVariogram2(v, nx, ny, nz, px, py, pz, 30.0, 5)
    (x_short, y_short, y_err_short), (x_sample, y_sample, y_err_sample) = ev.estimate_variogram(5000)

    plot_method = 2
    if plot_method == 0:
        # Plot empirical variogram, true variogram and realization

        plt.subplot(121)
        # plt.title('n+p={}, range={}'.format(nx + px, r))
        plt.title('Variogram estimation')
        plt.xlabel('Distance')
        plt.ylabel('Variogram value, $\gamma$')
        plt.plot(x_short, 0.5 * y_short, '.b', label='Empirical')
        plt.plot(x_sample, 0.5 * y_sample, '.b', label='_nolegend_')
        plt.grid()

        x_true = np.linspace(0, np.sqrt(nx ** 2 + ny ** 2 + nz ** 2), 100)
        y_true = [1.0 - v.corr(x) for x in x_true]
        plt.plot(x_true, y_true, '-k', label='True')
        plt.legend(loc=4)
        plt.xlim([0, 141])

        plt.subplot(122)
        plt.imshow(ev.s[:, :, int(ev.s.shape[2]/2)], interpolation='None')
        plt.title('Sample realization')

        plt.show()
    elif plot_method in [1, 2]:
        # Plot empirical variogram, true variogram and difference
        plt.rcParams['figure.figsize'] = [20, 10]
        plt.subplot(121)
        # plt.title('n+p={}, range={}'.format(nx + px, r))
        plt.title('Variogram estimation')
        plt.xlabel('Distance')
        plt.ylabel('Variogram value, $\gamma$')
        plt.plot(x_short, 0.5 * y_short, '.b', label='Empirical')
        plt.plot(x_sample, 0.5 * y_sample, '.b', label='_nolegend_')
        plt.grid()

        x_true = np.linspace(0, np.sqrt(nx ** 2 + ny ** 2 + nz ** 2), 100)
        y_true = [1.0 - v.corr(x) for x in x_true]
        plt.plot(x_true, y_true, '-k', label='True', lw=2)

        plt.xlim([0, 141])

        if plot_method == 2:
            # Include the smoothed variogram
            y_smooth = [1.0 - v.corr(x) * EmpiricalVariogram2.smoothing ** ((x/r)**2) for x in x_true]
            plt.plot(x_true, y_smooth, '-r', lw=2, label='Smoothed')
        plt.legend(loc=4)

        plt.subplot(122)
        diffs = []
        for x, y in zip(x_short, y_short):
            diffs.append(0.5*y - (1.0 - v.corr(x)))
        for x, y in zip(x_sample, y_sample):
            diffs.append(0.5*y - (1.0 - v.corr(x)))
        plt.plot(x_short + x_sample, diffs, '.b')
        plt.xlim([0, 141])
        plt.plot([0, 141], [0, 0], 'k', lw=2)
        plt.grid()
        plt.xlabel('Distance')
        yl = np.max(np.abs(diffs))
        plt.ylim([-yl, yl])
        plt.title('Difference')
        plt.show()

