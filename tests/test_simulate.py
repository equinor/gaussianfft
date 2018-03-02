import unittest
import nrlib


class TestSimulate(unittest.TestCase):
    def test_simulation_size_1d(self):
        v = nrlib.variogram('spherical', 100.0)
        a = nrlib.simulation_size(v, 100, 1.0)
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0], 201)

    def test_simulation_size_2d(self):
        v = nrlib.variogram('spherical', 2113.0, 997.0)
        a = nrlib.simulation_size(v, 132, 10.0, 657, 12.0)
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0], 406)
        self.assertEqual(a[1], 741)

    def test_simulation_size_3d_equal(self):
        v = nrlib.variogram('spherical', 1000.0, 1000.0, 1000.0)
        a = nrlib.simulation_size(v, 100, 10.0, 100, 10.0, 100, 10.0)
        self.assertEqual(len(a), 3)
        self.assertEqual(a[0], 201)
        self.assertEqual(a[1], 201)
        self.assertEqual(a[2], 201)

    def test_simulation_size_3d_uneven(self):
        v = nrlib.variogram('spherical', 1000.0, 250.0, 125.0)
        a = nrlib.simulation_size(v, 507, 50.0, 305, 17.0, 103, 4.0)
        self.assertEqual(len(a), 3)
        self.assertEqual(a[0], 528)
        self.assertEqual(a[1], 320)
        self.assertEqual(a[2], 135)


if __name__ == '__main__':
    unittest.main()
