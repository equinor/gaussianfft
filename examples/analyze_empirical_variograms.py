import matplotlib.pyplot as plt
import nrlib
import numpy as np
import os

import sys

from util.empirical_variogram2 import EmpiricalVariogram2


def run_analysis(output_folder):
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)
    vtypes = [
        'gaussian',
        'spherical',
        'exponential',
        'general_exponential',
        'matern32',
        'matern52',
        'matern72',
    ]

    EmpiricalVariogram2.smoothing = 1.0
    plt.rcParams['figure.figsize'] = [20, 10]
    for v in vtypes:
        print('Creating images for variogram type: ' + v)
        plt.clf()
        create_plots_for_vtype(output_folder, v)


def create_plots_for_vtype(output_folder, vtype):
    # Next steps:
    # - structured testing of the parameters. Verify the hypothesis that 4x range is sufficient
    # - 1D verification that the estimation is working as intended.
    nx, ny, nz = 100, 100, 1
    r = 100
    v = nrlib.variogram(vtype, r, r, r)
    ev = EmpiricalVariogram2(v, nx, ny, nz, -1, -1, -1, 30.0, 5)
    (x_short, y_short, y_err_short), (x_sample, y_sample, y_err_sample) = ev.estimate_variogram(5000)

    plt.subplot(121)
    # plt.title('n+p={}, range={}'.format(nx + px, r))
    plt.title('Variogram estimation')
    plt.xlabel('Distance')
    plt.ylabel('Variogram value, $\gamma$')
    plt.plot(x_short, 0.5 * y_short, '.b', label='Empirical')
    plt.plot(x_sample, 0.5 * y_sample, '.b', label='_nolegend_')
    plt.grid()

    x_true = np.linspace(0, np.sqrt(nx ** 2 + ny ** 2 + nz ** 2), 100)
    y_true = [1.0 - v.corr(x) for x in x_true]
    plt.plot(x_true, y_true, '-k', label='True', lw=2)

    plt.xlim([0, 141])
    plt.legend(loc=4)

    plt.subplot(122)
    diffs = []
    for x, y in zip(x_short, y_short):
        diffs.append(0.5 * y - (1.0 - v.corr(x)))
    for x, y in zip(x_sample, y_sample):
        diffs.append(0.5 * y - (1.0 - v.corr(x)))
    plt.plot(x_short + x_sample, diffs, '.b')
    plt.xlim([0, 141])
    plt.plot([0, 141], [0, 0], 'k', lw=2)
    plt.grid()
    plt.xlabel('Distance')
    yl = np.max(np.abs(diffs))
    plt.ylim([-yl, yl])
    plt.title('Difference')
    plt.savefig(os.path.join(output_folder, vtype + '.pdf'))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Provide one argument: output directory for output')
    else:
        run_analysis(sys.argv[1])
