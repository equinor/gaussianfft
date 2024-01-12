import numpy as np
import matplotlib.pyplot as plt
import gaussianfft as grf

grf.seed(123)

variogram = grf.variogram('exponential', main_range=1000, perp_range=1000)

nx = 100
ny = 100
x = np.linspace(1000.0, 2000.0, nx)
y = np.linspace(-3000.0, -1000.0, nx)

# Option A
field = grf.simulate(variogram, nx=nx, ny=nx, dx=1000.0 / nx, dy=2000.0 / ny)

plt.subplot(211)
plt.imshow(field.reshape((nx, ny)))
plt.title('Simulate 2D Gaussian field')
plt.colorbar()

plt.subplot(212)
plt.imshow(np.roll(field.reshape((nx, ny)), int(nx / 2), axis=0))
plt.title('The same field, shifted (should not be continuous)')
plt.colorbar()
plt.show()
