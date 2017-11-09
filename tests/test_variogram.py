import unittest
import nrlib


class TestVariogram(unittest.TestCase):
    def test_all_args(self):
        v = nrlib.variogram('exponential', 1000.0, 1000.0, 1000.0, 0.0, 0.0, 1.5)
        self.assertIsInstance(v, nrlib.Variogram)

    def test_missing_args(self):
        # Calls the factory function with only one argument ('exponential')
        self.assertRaises(Exception, nrlib.variogram, 'exponential')

    def test_only_range_args(self):
        nrlib.variogram('exponential', 1000.0, 1000.0, 1000.0)

    def test_dimensions(self):
        nrlib.variogram('exponential', 123, 456, 789)
        nrlib.variogram('exponential', 123, 456)
        nrlib.variogram('exponential', 123)

    def test_variogram_types(self):
        nrlib.variogram('constant', 1000.0)
        nrlib.variogram('gaussian', 1000.0)
        nrlib.variogram('exponential', 1000.0)
        nrlib.variogram('spherical', 1000.0)
        nrlib.variogram('general_exponential', 1000.0)
        nrlib.variogram('matern32', 1000.0)
        nrlib.variogram('matern52', 1000.0)
        nrlib.variogram('matern72', 1000.0)

    def test_specific_args(self):
        # Valid keywords
        nrlib.variogram('exponential', main_range=1000.0)
        nrlib.variogram('exponential', main_range=1000.0, perp_range=1000.0)
        nrlib.variogram('exponential', main_range=1000.0, depth_range=1000.0)
        nrlib.variogram('exponential', main_range=1000.0, azimuth=1000.0)
        nrlib.variogram('exponential', main_range=1000.0, dip=1000.0)
        nrlib.variogram('exponential', main_range=1000.0, power=1000.0)
        # Invalid keyword
        self.assertRaises(Exception, nrlib.variogram, 'exponential', main_range=1000.0, foo=1000.0)
        # Missing arguments
        self.assertRaises(Exception, nrlib.variogram, 'exponential')

    def test_correlation_function(self):
        v = nrlib.variogram('exponential', 1000.0, 500.0, 250.0)
        a = v.corr(1000)
        b = v.corr(0, 500)
        c = v.corr(0, 0, 250)
        self.assertAlmostEqual(a, b)
        self.assertAlmostEqual(b, c)


if __name__ == '__main__':
    unittest.main()
