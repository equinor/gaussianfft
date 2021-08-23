import unittest
import gaussianfft as grf


class TestVariogram(unittest.TestCase):
    def test_all_args(self):
        v = grf.variogram('exponential', 1000.0, 1000.0, 1000.0, 0.0, 0.0, 1.5)
        self.assertIsInstance(v, grf.Variogram)

    def test_missing_args(self):
        # Calls the factory function with only one argument ('exponential')
        self.assertRaises(Exception, grf.variogram, 'exponential')

    def test_only_range_args(self):
        grf.variogram('exponential', 1000.0, 1000.0, 1000.0)

    def test_dimensions(self):
        grf.variogram('exponential', 123, 456, 789)
        grf.variogram('exponential', 123, 456)
        grf.variogram('exponential', 123)

    def test_variogram_types(self):
        grf.variogram('constant', 1000.0)
        grf.variogram('gaussian', 1000.0)
        grf.variogram('exponential', 1000.0)
        grf.variogram('spherical', 1000.0)
        grf.variogram('general_exponential', 1000.0)
        grf.variogram('matern32', 1000.0)
        grf.variogram('matern52', 1000.0)
        grf.variogram('matern72', 1000.0)

    def test_specific_args(self):
        # Valid keywords
        grf.variogram('exponential', main_range=1000.0)
        grf.variogram('exponential', main_range=1000.0, perp_range=1000.0)
        grf.variogram('exponential', main_range=1000.0, depth_range=1000.0)
        grf.variogram('exponential', main_range=1000.0, azimuth=1000.0)
        grf.variogram('exponential', main_range=1000.0, dip=1000.0)
        grf.variogram('exponential', main_range=1000.0, power=1000.0)
        # Invalid keyword
        self.assertRaises(Exception, grf.variogram, 'exponential', main_range=1000.0, foo=1000.0)
        # Missing arguments
        self.assertRaises(Exception, grf.variogram, 'exponential')

    def test_correlation_function(self):
        v = grf.variogram('exponential', 1000.0, 500.0, 250.0)
        a = v.corr(1000)
        b = v.corr(0, 500)
        c = v.corr(0, 0, 250)
        self.assertAlmostEqual(a, b)
        self.assertAlmostEqual(b, c)


if __name__ == '__main__':
    unittest.main()
