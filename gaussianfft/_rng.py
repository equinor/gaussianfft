from operator import index
from numpy.random import RandomState
from _gaussianfft import seed as c_seed


numpy_rng = RandomState()


def seed(value=None):
    """Seed GaussianFFT's private RNG. Integer seeds must be between 0 and 2**32 - 1.
    With no argument, return the C++ start seed without changing either RNG,
    unless NonstationaryVariogram.simulate() has been called with shared noise.
    The GaussianFFT streams are not isolated between threads or callers.
    """
    if value is None:
        return c_seed()
    value = index(value)
    if not 0 <= value < 2**32:
        raise ValueError("Seed must be between 0 and 2**32 - 1")
    c_seed(value)
    numpy_rng.seed(value)
