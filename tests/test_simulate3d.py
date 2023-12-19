import pytest
import gaussianfft as grf
import numpy as np

@pytest.fixture
def simulated_field():
    variogram = grf.variogram('exponential', 500, 375, 250)
    nx = 100
    ny = 50
    nz = 25
    dx = 10.0
    dy = 17.5
    dz = 25.0
    grf.seed(12321)
    field3d = grf.simulate(variogram, nx, dx, ny, dy, nz, dz).reshape((nx, ny, nz), order='F')
    assert field3d.shape == (nx, ny, nz)
    return field3d, nx, ny, nz

def test_gradient(simulated_field):
    field, _, _, _ = simulated_field
    diffs0 = np.diff(field, axis=0)
    diffs1 = np.diff(field, axis=1)
    diffs2 = np.diff(field, axis=2)

    assert np.abs(np.mean(diffs0)) <= 0.15
    assert np.abs(np.mean(diffs1)) <= 0.15
    assert np.abs(np.mean(diffs2)) <= 0.15

    assert np.std(diffs0) < 0.37
    assert np.std(diffs1) < 0.53
    assert np.std(diffs2) < 0.75

    assert np.std(diffs0) < np.std(diffs1)
    assert np.std(diffs1) < np.std(diffs2)

    assert np.max(np.abs(diffs0)) < 5 * np.std(diffs0)
    assert np.max(np.abs(diffs1)) < 5 * np.std(diffs1)
    assert np.max(np.abs(diffs2)) < 5 * np.std(diffs2)

def test_rolled_gradient(simulated_field):
    # When rolling the field, there should be a spike in the gradient data. Otherwise, the padding used for fft
    # was insufficient
    field, nx, ny, nz = simulated_field
    diffs0 = np.diff(np.roll(field, int(nx/2), axis=0), axis=0)
    diffs1 = np.diff(np.roll(field, int(ny/2), axis=1), axis=1)
    diffs2 = np.diff(np.roll(field, int(nz/2), axis=2), axis=2)

    # Check that most of the rolled max diffs occur at the rolled index. Most meaning more than 20 % of the
    # points. This is accurate enough to pick up if the fft does not pad correctly, but should perhaps be replaced
    # by a more robust test
    amax = np.argmax(np.abs(diffs0), axis=0)
    assert np.count_nonzero(amax != int(nx/2 - 1)) < amax.size * 0.8

    amax = np.argmax(np.abs(diffs1), axis=1)
    assert np.count_nonzero(amax != int(ny/2 - 1)) < amax.size * 0.8

    amax = np.argmax(np.abs(diffs2), axis=2)
    assert np.count_nonzero(amax != int(nz/2 - 1)) < amax.size * 0.8
