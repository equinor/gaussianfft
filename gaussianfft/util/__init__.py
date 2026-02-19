from importlib.util import find_spec

if find_spec('scipy') is None:
    raise ImportError('Scipy is not installed, and is required to use these utilities')

from gaussianfft.util.empirical_variogram import EmpiricalVariogram
from gaussianfft.util.padding_analyzer import PaddingAnalyzer, PaddingAnalyzerDefaults

__all__ = ['EmpiricalVariogram', 'PaddingAnalyzer', 'PaddingAnalyzerDefaults']
