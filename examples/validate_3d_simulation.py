import matplotlib.pyplot as plt
import numpy as np

import gaussianfft as grf


def example_cube():
    grf.seed(123)
    variogram = grf.variogram('gaussian', 100, 100, 100, 0.0, 0.0, 1.5)
    # nx, ny, nz = 100, 100, 100
    nx, ny, nz = 127, 127, 127
    dx, dy, dz = 2, 2, 2
    field = grf.advanced.simulate(variogram, nx, dx, ny, dy, nz, dz, padx=-1, pady=-1, padz=-1)
    field3d = np.array(field).reshape((nx, ny, nz), order='F')
    lin = np.arange(0, nx) * dx
    plot_3d_mid_slices(field3d, lin, lin, lin)
    plt.show()


def example_box():
    grf.seed(123)
    az = 90.0
    dip = 30.0
    variogram = grf.variogram('exponential', 1000, 1000, 100, az, dip, 1.5)
    nx, ny, nz = 100, 50, 25
    dx, dy, dz = 10, 10, 10
    field = grf.simulate(variogram, nx, dx, ny, dy, nz, dz)
    field3d = np.array(field).reshape((nx, ny, nz), order='F')
    lin_x = np.arange(0, nx) * dx
    lin_y = np.arange(0, ny) * dy
    lin_z = np.arange(0, nz) * dz
    fig = plot_3d_mid_slices(field3d, lin_x, lin_y, lin_z)
    fig.suptitle(f'Azimuth = {az}, Dip = {dip}')
    plt.show()


def plot_3d_using_imshow(field3d):
    plt.subplot(131)
    nx, ny, nz = field3d.shape
    plt.imshow(field3d[int(nx / 2), :, :], interpolation='None')
    plt.colorbar(orientation='horizontal')
    plt.title('x-slice')

    plt.subplot(132)
    plt.imshow(field3d[:, int(ny / 2), :], interpolation='None')
    plt.colorbar(orientation='horizontal')
    plt.title('y-slice')

    plt.subplot(133)
    plt.imshow(field3d[:, :, int(nz / 2)], interpolation='None')
    plt.colorbar(orientation='horizontal')
    plt.title('z-slice')

    plt.show()


def plot_3d_mid_slices(field3d, lin_x, lin_y, lin_z):
    fig = plt.figure()

    ax1 = fig.add_subplot(131)
    nx, ny, nz = field3d.shape
    ax1.contourf(lin_y, lin_z, field3d[int(nx / 2), :, :].T, 30)
    ax1.set_aspect('equal')
    ax1.set_xlabel('E')
    ax1.set_ylabel('Z')
    ax1.set_title('x-slice/North-slice')

    ax2 = fig.add_subplot(132)
    ax2.contourf(lin_x, lin_z, field3d[:, int(ny / 2), :].T, 30)
    ax2.set_aspect('equal')
    ax2.set_xlabel('N')
    ax2.set_ylabel('Z')
    ax2.set_title('y-slice/East-slice')

    ax3 = fig.add_subplot(133)
    ax3.contourf(lin_y, lin_x, field3d[:, :, int(nz / 2)], 30)
    ax3.set_aspect('equal')
    ax3.set_xlabel('E')
    ax3.set_ylabel('N')
    ax3.set_title('z-slice')

    fig.tight_layout()
    return fig


if __name__ == '__main__':
    import sys

    examples = {
        'box': example_box,
        'cube': example_cube,
    }
    if len(sys.argv) != 2 or sys.argv[1] not in examples:
        print('Run as')
        print('  [python] {} <example>'.format('validate_3d_simulation'))
        print('')
        print('  <example> being one of:')
        for f in examples.keys():
            print('    ' + f)
    else:
        examples[sys.argv[1]]()
