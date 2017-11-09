import unittest
import nrlib
import numpy as np


class TestSimulate3D(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        variogram = nrlib.variogram('exponential', 500, 375, 250)
        cls.nx = 100
        cls.ny = 50
        cls.nz = 25
        cls.dx = 10.0
        cls.dy = 17.5
        cls.dz = 25.0
        nrlib.seed(12321)
        cls.field3d = nrlib.simulate(variogram, cls.nx, cls.dx, cls.ny, cls.dy, cls.nz, cls.dz)
        cls.field_as_array = np.array(cls.field3d).reshape((cls.nx, cls.ny, cls.nz), order='F')

    def test_shape(self):
        self.assertTupleEqual(self.field_as_array.shape, (self.nx, self.ny, self.nz))

    def test_gradient(self):
        diffs0 = np.diff(self.field_as_array, axis=0)
        diffs1 = np.diff(self.field_as_array, axis=1)
        diffs2 = np.diff(self.field_as_array, axis=2)
        self.assertAlmostEqual(0.0, np.mean(diffs0), delta=0.15)
        self.assertAlmostEqual(0.0, np.mean(diffs1), delta=0.15)
        self.assertAlmostEqual(0.0, np.mean(diffs2), delta=0.15)
        self.assertLess(np.std(diffs0), 0.37)
        self.assertLess(np.std(diffs1), 0.53)
        self.assertLess(np.std(diffs2), 0.75)
        self.assertLess(np.std(diffs0), np.std(diffs1))
        self.assertLess(np.std(diffs1), np.std(diffs2))
        self.assertLess(np.max(np.abs(diffs0)), 5 * np.std(diffs0))
        self.assertLess(np.max(np.abs(diffs1)), 5 * np.std(diffs1))
        self.assertLess(np.max(np.abs(diffs2)), 5 * np.std(diffs2))

    def test_rolled_gradient(self):
        # When rolling the field, there should be a spike in the gradient data. Otherwise, the padding used for fft
        # was insufficient
        diffs0 = np.diff(np.roll(self.field_as_array, int(self.nx/2), axis=0), axis=0)
        diffs1 = np.diff(np.roll(self.field_as_array, int(self.ny/2), axis=1), axis=1)
        diffs2 = np.diff(np.roll(self.field_as_array, int(self.nz/2), axis=2), axis=2)
        amax = np.argmax(np.abs(diffs0), axis=0)
        # Check that most of the rolled max diffs occur at the rolled index. Most meaning more than 20 % of the
        # points. This is accurate enough to pick up if the fft does not pad correctly, but should perhaps be replaced
        # by a more robust test
        self.assertLess(
            np.count_nonzero(amax != int(self.nx/2 - 1)),
            amax.size * 0.8
        )
        amax = np.argmax(np.abs(diffs1), axis=1)
        self.assertLess(
            np.count_nonzero(amax != int(self.ny/2 - 1)),
            amax.size * 0.8
        )
        amax = np.argmax(np.abs(diffs2), axis=2)
        self.assertLess(
            np.count_nonzero(amax != int(self.nz/2 - 1)),
            amax.size * 0.8
        )


if __name__ == '__main__':
    unittest.main()
