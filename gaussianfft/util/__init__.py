try:
    import scipy
except ImportError:
    raise ImportError("Scipy is not installed, and is required to use these utilities")

from gaussianfft.util.empirical_variogram import EmpiricalVariogram
from gaussianfft.util.padding_analyzer import PaddingAnalyzerDefaults, PaddingAnalyzer

__all__ = ['EmpiricalVariogram', 'PaddingAnalyzer', 'PaddingAnalyzerDefaults']
