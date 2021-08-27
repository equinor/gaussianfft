from time import perf_counter

import numpy as np
import gaussianfft

from gaussianfft.util import EmpiricalVariogram


class PaddingAnalyzerDefaults:
    DRF = 1.0
    L = 1000
    n = 100
    seed = 12313
    nmax = 600
    ndims = 1


class PaddingAnalyzer:
    """
    Class for analyzing the relationship between range and padding and how it affects the estimation of the true
    variogram.
    """
    def __init__(self, desired_range, desired_padding_f, L=None, n=None, drf=None, nmax=None, vtype='gaussian',
                 seed=None, ndims=None):
        # Get default values
        n = n or PaddingAnalyzerDefaults.n
        drf = drf or PaddingAnalyzerDefaults.DRF
        L = L or PaddingAnalyzerDefaults.L
        seed = seed or PaddingAnalyzerDefaults.seed
        nmax = nmax or PaddingAnalyzerDefaults.nmax
        ndims = ndims or PaddingAnalyzerDefaults.ndims

        # Constants that potentially can be moved to input
        self._reference_strategy = 'origo'
        self._convergence_step = 10
        # Setup
        gaussianfft.seed(seed)
        d = L / n
        dr = drf * d

        # Convert from aprx pl to exact
        output_padding = []  # Actual padding (in number of gridcells)
        for p in desired_padding_f:
            output_padding.append(int((p * L) / d))

        # Prepare results
        v, ev = self.create_variograms(desired_range[0], output_padding[0], ndims, d, n, L, vtype)
        refs = ev.pick_reference_points(self._reference_strategy)
        mid, _, _, _, convrg = ev.estimate_variogram(nmax, dr, refs, analyze_convergence=self._convergence_step)
        # -----

        self.deltas = np.zeros((len(output_padding), len(desired_range), convrg.deltas.shape[1]))
        t0 = perf_counter()
        for i, r in enumerate(desired_range):
            print("*** {}/{} ***".format(i, len(desired_range)))
            print("  Total time spent: {:.2f}".format(perf_counter() - t0))
            for j, p in enumerate(output_padding):
                v, ev = self.create_variograms(r, p, ndims, d, n, L, vtype)
                refs = ev.pick_reference_points('origo')
                mid, _, _, _, convrg = ev.estimate_variogram(nmax, dr, refs, analyze_convergence=self._convergence_step)
                self.deltas[j, i, :] = convrg.deltas[-1]

        self.range = desired_range
        self.padding_f = np.array(output_padding) / n
        self.grid = np.linspace(0, self.deltas.shape[2] * d, self.deltas.shape[2])

    def create_variograms(self, rrange, padding, ndims, d, n, L, vtype):
        if ndims == 1:
            v = gaussianfft.variogram(vtype, rrange * L)
            ev = EmpiricalVariogram(v, n, d, 1, 0, 1, 0, padding, padding, padding)
        elif ndims == 2:
            v = gaussianfft.variogram(vtype, rrange * L, rrange * L)
            ev = EmpiricalVariogram(v, n, d, n, d, 1, 0, padding, padding, padding)
        else:
            raise NotImplementedError("Padding analyzer is not implemented for {} dimensions.".format(ndims))
        return v, ev
