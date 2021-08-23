import gaussianfft.advanced
import numpy as np
from time import perf_counter


class ResourceExtrapolator:
    def __init__(self, nmin=8, nmax=64, nstep=8, ndims=2):
        self.nmin = nmin
        self.nmax = nmax
        self.nstep = nstep
        self.ndims = ndims

        # Constants
        self._grid_length = 1000.0
        self._variogram_range = 500.0

    def extrapolate(self, ex_nmax, vtype):
        data = self.generate(vtype)
        data_array = np.array(data)
        x = data_array[:, 0] ** self.ndims
        y = data_array[:, 1]
        ls_sol = np.linalg.lstsq(x.reshape(x.size, 1), y)
        return x, y, ls_sol[0][0]

    def generate(self, vtype='exponential'):
        vario = gaussianfft.variogram(vtype, self._variogram_range)
        data = []
        for n in range(self.nmin, self.nmax + 1, self.nstep):
            t0 = perf_counter()
            self._simulate(vario, n)
            t1 = perf_counter() - t0
            print('{:4}: {} s'.format(n, t1))
            data.append((n, t1))
        return data

    def _simulate(self, vario, n):
        d = self._grid_length / (n - 1)
        gaussianfft.advanced.simulate(vario,
                                n,
                                d,
                                n if self.ndims > 1 else 1,
                                d,
                                n if self.ndims > 2 else 1,
                                d,
                                padx=n,
                                pady=n,
                                padz=n)


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    re = ResourceExtrapolator(nmin=16, nmax=256, nstep=16, ndims=3)
    en = 512
    x, y, sol = re.extrapolate(en, 'exponential')
    plt.loglog(x, y, 'o')
    lref = 1000
    plt.loglog([lref, en ** re.ndims], [sol * lref, sol * en ** re.ndims])
    plt.title('Line/Square/Cube simulation time')
    plt.legend(['Data', 'Extrapolated'], loc=4)
    plt.xlabel('Number of cells (before padding)')
    plt.ylabel('Time (s)')
    plt.grid()
    plt.show()
