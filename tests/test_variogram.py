import unittest
import numpy as np
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

    def test_corr_array_matches_scalar(self):
        rng = np.random.default_rng(42)
        for kind in grf.VariogramType:
            variogram = grf.variogram(kind, 1000.0, 500.0, 250.0, 30.0, 20.0)
            for ndims in (1, 2, 3):
                displacements = rng.uniform(-1000.0, 1000.0, (20, ndims))
                displacements[0] = 0.0
                for values in (displacements, np.asfortranarray(displacements),
                               displacements[-2::-2, ::-1], displacements.astype(np.float32),
                               displacements.astype(np.int64)):
                    with self.subTest(kind=kind, ndims=ndims, strides=values.strides,
                                      dtype=values.dtype):
                        expected = [variogram.corr(*row) for row in values]
                        actual = variogram.corr_array(values)
                        self.assertEqual(actual.shape, (len(values),))
                        self.assertEqual(actual.dtype, np.dtype('float64'))
                        np.testing.assert_allclose(actual, expected, rtol=1e-14, atol=1e-14)

    def test_corr_array_empty(self):
        variogram = grf.variogram('exponential', 1000.0)
        for ndims in (1, 2, 3):
            self.assertEqual(variogram.corr_array(np.empty((0, ndims))).shape, (0,))

    def test_corr_array_invalid_shape(self):
        variogram = grf.variogram('exponential', 1000.0)
        for shape in ((), (3,), (2, 0), (2, 4), (2, 2, 2)):
            with self.subTest(shape=shape):
                with self.assertRaisesRegex(ValueError, 'displacements must have shape'):
                    variogram.corr_array(np.zeros(shape))


if __name__ == '__main__':
    unittest.main()
