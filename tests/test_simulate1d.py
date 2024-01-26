import pytest
import gaussianfft as grf
import numpy as np
import numpy.typing as npt

def _cov_mat_genexp(range_: int, n: int, distance: int) -> npt.NDArray[np.double]:
    """Generate covariance matrix based on a general exponential model.
    """
    c = np.array([((n - i) * distance / range_) ** 1.8 for i in range(2 * n + 1)])
    c = np.exp(-3 * np.abs(c))
    s = np.zeros((n, n))
    for i in range(n):
        s[i, :] = c[n - i:2 * n - i]
    return s

# Values for the tests below have been set based on the specific seed being used above. Using a random seed could
# cause the tests to fail from time to time.

@pytest.fixture
def simulated_field():
    variogram = grf.variogram('gaussian', 1000)
    nx = 500
    dx = 1.0
    grf.seed(12321)
    field =  grf.simulate(variogram, nx, dx)
    assert field.shape == (nx, )
    return field, nx

def test_gradient(simulated_field):
    field, _ = simulated_field
    diffs = np.diff(field)
    assert np.isclose(0.0, np.mean(diffs), atol=1e-2), "The field should not have any overall directional trend"
    assert np.std(diffs) < 0.1, "Changes between consecutive points should be small and consistent, indicating a relatively smooth field without large, abrupt changes"
    assert np.max(np.abs(diffs)) < 5 * np.std(diffs), "There should be no large jumps in the field"

def test_rolled_gradient(simulated_field):
    # When rolling the field, there should be a spike in the gradient data. Otherwise, the padding used for fft
    # was insufficient
    field, nx = simulated_field
    diffs = np.diff(np.roll(field, int(nx/2)))
    assert np.argmax(np.abs(diffs)) == int(nx/2) - 1, "Largest spike in gradient should occur exactly at the point where the field was rolled"
    assert np.max(np.abs(diffs)) > 15 * np.std(diffs), "Rolling should cause significant changes to the gradient"

def test_chi2():
    # A multivariate normal vector, x, with covariance matrix S, shall satisfy x'(S^-1)x ~ chi2(x.size)
    # This test makes an approximate check of this assumption. Parameters are taken from a Hufsa case.
    from scipy.stats import chi2
    nx = 40
    Lx = 8222
    rx = 6106
    power = 1.8
    dx = Lx / (nx - 1)
    S = _cov_mat_genexp(rx, nx, dx)
    v = grf.variogram('general_exponential', rx, power=power)
    z = []
    grf.seed(41414)
    for _ in range(3000):
        _x = grf.simulate(v, nx, dx)
        z.append(np.inner(_x, np.linalg.solve(S, _x)))

    # Compare distributions
    df = nx
    nbins = 30
    x = np.linspace(chi2.ppf(0.01, df), chi2.ppf(0.99, df), nbins)
    dxx = x[1] - x[0]
    true_chi2 = chi2.pdf(x, df)
    esti_chi2 = np.histogram(z, nbins, range=(x[0] - dxx, x[-1] + dxx), density=True)[0]
    assert np.linalg.norm(true_chi2 - esti_chi2) < 0.02  # Tolerance set by regression
