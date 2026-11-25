"""Plot a 2D Gaussian field with gridded azimuths and one synthetic observation."""

import matplotlib.pyplot as plt
import numpy as np

import gaussianfft as grf

grf.seed(42)
shape = (101, 101)
spacing = (10.0, 10.0)
azimuths = np.tile(np.linspace(0.0, 60.0, shape[1]), (shape[0], 1))
variogram = grf.nonstationary_variogram(
    'matern52',
    main_range=120.0,
    perp_range=20.0,
    gridded_azimuth_values=azimuths,
    gridded_azimuth_spacing=spacing,
)

field, = grf.conditional_simulate(
    variogram, shape, spacing,
    obs_locations=np.array([[500.0, 500.0]]),
    obs_values=np.array([4.0]),
    obs_uncertainties=np.array([0.0]),
)

plt.imshow(field.T, origin='lower', cmap='RdBu_r')
plt.title('2D non-stationary field conditioned at the center')
plt.colorbar()
plt.show()
