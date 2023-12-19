import gaussianfft as grf

def test_simulation_size_1d():
    v = grf.variogram('spherical', 100.0)
    a = grf.simulation_size(v, 100, 1.0)
    assert len(a) == 1
    assert a[0] == 201

def test_simulation_size_2d():
    v = grf.variogram('spherical', 2113.0, 997.0)
    a = grf.simulation_size(v, 132, 10.0, 657, 12.0)
    assert len(a) == 2
    assert a[0] == 406
    assert a[1] == 741

def test_simulation_size_3d_equal():
    v = grf.variogram('spherical', 1000.0, 1000.0, 1000.0)
    a = grf.simulation_size(v, 100, 10.0, 100, 10.0, 100, 10.0)
    assert len(a) == 3
    assert a[0] == 201
    assert a[1] == 201
    assert a[2] == 201

def test_simulation_size_3d_uneven():
    v = grf.variogram('spherical', 1000.0, 250.0, 125.0)
    a = grf.simulation_size(v, 507, 50.0, 305, 17.0, 103, 4.0)
    assert len(a) == 3
    assert a[0] == 528
    assert a[1] == 320
    assert a[2] == 135
