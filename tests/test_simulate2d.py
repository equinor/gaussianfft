import unittest
import nrlib
import numpy as np


class TestSimulate3D(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        variogram = nrlib.variogram('exponential', 1000, 500, 250.0)
        cls.nx = 100
        cls.ny = 50
        cls.dx = 1.0
        cls.dy = 1.5
        nrlib.seed(12321)
        cls.field3d = nrlib.simulate(variogram, cls.nx, cls.dx, cls.ny, cls.dy)
        cls.field_as_array = np.array(cls.field3d).reshape((cls.nx, cls.ny), order='F')

    def test_shape(self):
        self.assertTupleEqual(self.field_as_array.shape, (self.nx, self.ny))

    def test_gradient(self):
        diffs0 = np.diff(self.field_as_array, axis=0)
        diffs1 = np.diff(self.field_as_array, axis=1)
        self.assertAlmostEqual(0.0, np.mean(diffs0), delta=0.15)
        self.assertAlmostEqual(0.0, np.mean(diffs1), delta=0.15)
        self.assertLess(np.std(diffs0), 0.1)
        self.assertLess(np.std(diffs1), 0.15)
        # Step length is longer in the y direction, so the standard deviation must be larger in that direction
        self.assertLess(np.std(diffs0), np.std(diffs1))
        self.assertLess(np.max(np.abs(diffs0)), 5 * np.std(diffs0))
        self.assertLess(np.max(np.abs(diffs1)), 5 * np.std(diffs1))

    def test_rolled_gradient(self):
        # When rolling the field, there should be a spike in the gradient data. Otherwise, the padding used for fft
        # was insufficient
        diffs0 = np.diff(np.roll(self.field_as_array, int(self.nx/2), axis=0), axis=0)
        diffs1 = np.diff(np.roll(self.field_as_array, int(self.ny/2), axis=1), axis=1)
        self.assertLess(
            np.count_nonzero(np.argmax(np.abs(diffs0), axis=0) != int(self.nx/2 - 1)),
            self.ny/3
        )
        self.assertLess(
            np.count_nonzero(np.argmax(np.abs(diffs1), axis=1) != int(self.ny/2 - 1)),
            self.nx/3
        )


if __name__ == '__main__':
    unittest.main()
