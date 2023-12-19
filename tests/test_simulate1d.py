import unittest
import gaussianfft as grf
import numpy as np


def _cov_mat_genexp(r, n, d):
    c = np.array([((n - i) * d / r) ** 1.8 for i in range(2 * n + 1)])
    c = np.exp(-3 * np.abs(c))
    s = np.zeros((n, n))
    for i in range(n):
        s[i, :] = c[n - i:2 * n - i]
    return s


class TestSimulate3D(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        variogram = grf.variogram('gaussian', 1000)
        cls.nx = 500
        cls.dx = 1.0
        grf.seed(12321)
        cls.field = grf.simulate(variogram, cls.nx, cls.dx)

    def test_shape(self):
        self.assertTupleEqual(self.field.shape, (self.nx,))

    # Values for the tests below have been set based on the specific seed being used above. Using a random seed could
    # cause the tests to fail from time to time.

    def test_gradient(self):
        diffs = np.diff(self.field)
        self.assertAlmostEqual(0.0, np.mean(diffs), places=2)
        self.assertLess(np.std(diffs), 0.1)
        self.assertLess(np.max(np.abs(diffs)), 5 * np.std(diffs))

    def test_rolled_gradient(self):
        # When rolling the field, there should be a spike in the gradient data. Otherwise, the padding used for fft
        # was insufficient
        diffs = np.diff(np.roll(self.field, int(self.nx/2)))
        self.assertEqual(np.argmax(np.abs(diffs)), int(self.nx/2) - 1)
        self.assertGreater(np.max(np.abs(diffs)), 15 * np.std(diffs))

    def test_chi2(self):
        # A multivariate normal vector, x, with covariance matrix S, shall satisfy x'(S^-1)x ~ chi2(x.size)
        # This test makes an approximate check of this assumption. Parameters are taken from a Hufsa case.
        from scipy.stats import chi2
        nx = 40
        Lx = 8222  # 7796
        rx = 6106
        power = 1.8
        dx = Lx / (nx - 1)
        c = _cov_mat_genexp(rx, nx, dx)
        v = grf.variogram('general_exponential', rx, power=power)
        z = []
        grf.seed(41414)
        for i in range(3000):
            f = grf.simulate(v, nx, dx)
            z.append(np.inner(f, np.linalg.solve(c, f)))

        # Compare distributions
        df = nx
        nbins = 30
        x = np.linspace(chi2.ppf(0.01, df), chi2.ppf(0.99, df), nbins)
        dxx = x[1] - x[0]
        true_chi2 = chi2.pdf(x, df)
        esti_chi2 = np.histogram(z, nbins, range=(x[0] - dxx, x[-1] + dxx), density=True)[0]
        self.assertLess(np.linalg.norm(true_chi2 - esti_chi2), 0.02)  # Tolerance set by regression


if __name__ == '__main__':
    unittest.main()
