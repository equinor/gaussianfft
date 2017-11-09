import numpy as np
import matplotlib.pyplot as plt
import gaussfft

gaussfft.seed(123)

# Option A:
variogram1 = gaussfft.ExponentialVariogram(xrange=1000, yrange=1000)
# Option B (tror denne er å foretrekke da det er naturlig å kunne legge navn i en liste hvis en ønsker iterasjon):
# variogram2 = gaussfft.variogram.create('exponential', xrange=1000, yrange=1000)
variogram2 = gaussfft.variogram('exponential', xrange=1000, yrange=1000)
# Option C (Hvis vi ikke ønsker hierarki av Variogram-klassen)
variogram3 = gaussfft.Variogram(xrange=1000, yrange=1000, correlation=lambda x, y: x-y)

nx = 100
ny = 100
x = np.linspace(1000.0, 2000.0, nx)
y = np.linspace(-3000.0, -1000.0, nx)

# Option A
field1 = gaussfft.simulate2d(variogram1, nx=nx, ny=nx, dx=1000.0/nx, dy=2000.0/ny)
# Option B
field2 = gaussfft.simulate2d(variogram1, xlen=100, ylen=100, dx=10.0, dy=10.0)
# Option C
field3 = gaussfft.simulate2d(variogram1, xlen=100, ylen=100, nx=10, ny=10)

plt.subplot(211)
plt.imshow(x, y, field1)
plt.title('Simulate 2D Gaussian field')
plt.colorbar()

plt.subplot(212)
plt.imshow(np.roll(field1, int(nx/2), axis=0))
plt.title('The same field, shifted (should not be continuous)')
plt.colorbar()
plt.show()
