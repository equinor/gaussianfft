import unittest
import nrlib


class TestSimulate(unittest.TestCase):
    def test_simulation_size_1d(self):
        v = nrlib.variogram('spherical', 100.0)
        a = nrlib.simulation_size(v, 100, 1.0)
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0], 400)

    def test_simulation_size_2d(self):
        v = nrlib.variogram('spherical', 2113.0, 997.0)
        a = nrlib.simulation_size(v, 132, 10.0, 657, 12.0)
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0], 845)
        self.assertEqual(a[1], 740)

    def test_simulation_size_3d_equal(self):
        v = nrlib.variogram('spherical', 1000.0, 1000.0, 1000.0)
        a = nrlib.simulation_size(v, 100, 10.0, 100, 10.0, 100, 10.0)
        self.assertEqual(len(a), 3)
        self.assertEqual(a[0], 400)
        self.assertEqual(a[1], 400)
        self.assertEqual(a[2], 400)

    def test_simulation_size_3d_uneven(self):
        v = nrlib.variogram('spherical', 1000.0, 250.0, 125.0)
        a = nrlib.simulation_size(v, 507, 50.0, 305, 17.0, 103, 4.0)
        self.assertEqual(len(a), 3)
        self.assertEqual(a[0], 527)
        self.assertEqual(a[1], 319)
        self.assertEqual(a[2], 134)


if __name__ == '__main__':
    unittest.main()
