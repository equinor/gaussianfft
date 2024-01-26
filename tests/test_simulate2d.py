import pytest
import gaussianfft as grf
import numpy as np

@pytest.fixture
def simulated_field():
    variogram = grf.variogram('exponential', 1000, 500, 250.0)
    nx = 100
    ny = 50
    dx = 1.0
    dy = 1.5
    grf.seed(12321)
    field2d = grf.simulate(variogram, nx, dx, ny, dy).reshape((nx, ny), order='F')
    assert field2d.shape == (nx, ny)
    return field2d, nx, ny

def test_gradient(simulated_field):
    field, _, _ = simulated_field
    diffs0 = np.diff(field, axis=0)
    diffs1 = np.diff(field, axis=1)

    assert np.abs(np.mean(diffs0)) <= 0.15
    assert np.abs(np.mean(diffs1)) <= 0.15

    assert np.std(diffs0) < 0.1
    assert np.std(diffs1) < 0.15

    # Step length is longer in the y direction, so the standard deviation must be larger in that direction
    assert np.std(diffs0) < np.std(diffs1)

    assert np.max(np.abs(diffs0)) < 5 * np.std(diffs0)
    assert np.max(np.abs(diffs1)) < 5 * np.std(diffs1)

def test_rolled_gradient(simulated_field):
    field, nx, ny = simulated_field
    # When rolling the field, there should be a spike in the gradient data. Otherwise, the padding used for fft
    # was insufficient
    diffs0 = np.diff(np.roll(field, int(nx/2), axis=0), axis=0)
    diffs1 = np.diff(np.roll(field, int(ny/2), axis=1), axis=1)
    assert np.count_nonzero(np.argmax(np.abs(diffs0), axis=0) != int(nx/2 - 1)) < ny/2
    assert np.count_nonzero(np.argmax(np.abs(diffs1), axis=1) != int(ny/2 - 1)) < nx/3
