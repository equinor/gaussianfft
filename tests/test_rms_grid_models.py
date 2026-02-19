import unittest

import numpy as np

import gaussianfft as grf

"""
The contents of these tests are intended to be able to run in RMS as well simply by copying the contents without
modification, the exception being that import statements must be included and self.assert... does not make sense
outside a test class context.
"""


class TestRmsGridModels(unittest.TestCase):
    def test_grid_dimensions_to_run_simulation(self):
        try:
            d = project.grid_models['Heterogeneity'].get_grid().grid_indexer.dimensions
        except NameError:
            # Not in RMS context, use other values instead
            d = (90, 120, 45)
        v = grf.variogram('matern52', 312.0, 312.0, 312.0)
        grf.seed(1323)
        f_vec = grf.simulate(v, d[0], 20.0, d[1], 20.0, d[2], 20.0)
        f = np.array(f_vec).reshape(d, order='F')
        # Regression:
        self.assertAlmostEqual(f[11 + 10, 22 + 10, 13 + 10], -1.9465313106735047, 2)
        self.assertAlmostEqual(f[11 + 20, 22 + 20, 13 + 20], 0.35996944560911442, 2)
        self.assertAlmostEqual(f[11 + 30, 22 + 30, 13 + 30], -2.5241606022960497, 2)


if __name__ == '__main__':
    unittest.main()
