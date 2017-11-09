import unittest
# import sys; sys.path.insert(0, 'C:\Projects\GaussFFT')  # For debugging only
import nrlib
import numpy as np


class TestSimulate3D(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        variogram = nrlib.variogram('gaussian', 1000)
        cls.nx = 500
        cls.dx = 1.0
        nrlib.seed(12321)
        cls.field = nrlib.simulate(variogram, cls.nx, cls.dx)
        cls.field_as_array = np.array(cls.field)

    def test_shape(self):
        self.assertTupleEqual(self.field_as_array.shape, (self.nx,))

    # Values for the tests below have been set based on the specific seed being used above. Using a random seed could
    # cause the tests to fail from time to time.

    def test_gradient(self):
        diffs = np.diff(self.field_as_array)
        self.assertAlmostEqual(0.0, np.mean(diffs), places=2)
        self.assertLess(np.std(diffs), 0.1)
        self.assertLess(np.max(np.abs(diffs)), 5 * np.std(diffs))

    def test_rolled_gradient(self):
        # When rolling the field, there should be a spike in the gradient data. Otherwise, the padding used for fft
        # was insufficient
        diffs = np.diff(np.roll(self.field_as_array, int(self.nx/2)))
        self.assertEqual(np.argmax(np.abs(diffs)), int(self.nx/2) - 1)
        self.assertGreater(np.max(np.abs(diffs)), 15 * np.std(diffs))


if __name__ == '__main__':
    unittest.main()
