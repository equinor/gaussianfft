import numpy as np
import matplotlib.pyplot as plt
import nrlib


def example_cube():
    nrlib.seed(123)
    variogram = nrlib.variogram('gaussian', 100, 100, 100, 0.0, 0.0, 1.5)
    # nx, ny, nz = 100, 100, 100
    nx, ny, nz = 127, 127, 127
    dx, dy, dz = 2, 2, 2
    field = nrlib.advanced.simulate(variogram, nx, dx, ny, dy, nz, dz, padx=0, pady=0, padz=0)
    field3d = np.array(field).reshape((nx, ny, nz), order='F')
    plot_3d_mid_slices(field3d)


def example_box():
    nrlib.seed(123)
    variogram = nrlib.variogram('exponential', 1000, 1000, 1000, 0.0, 0.0, 1.5)
    nx, ny, nz = 100, 50, 25
    dx, dy, dz = 10, 10, 10
    field = nrlib.simulate(variogram, nx, dx, ny, dy, nz, dz)
    field3d = np.array(field).reshape((nx, ny, nz), order='F')
    plot_3d_mid_slices(field3d)


def plot_3d_mid_slices(field3d):
    plt.subplot(131)
    nx, ny, nz = field3d.shape
    plt.imshow(field3d[int(nx/2), :, :], interpolation='None')
    plt.colorbar(orientation='horizontal')
    plt.title('x-slice')

    plt.subplot(132)
    plt.imshow(field3d[:, int(ny/2), :], interpolation='None')
    plt.colorbar(orientation='horizontal')
    plt.title('y-slice')

    plt.subplot(133)
    plt.imshow(field3d[:, :, int(nz/2)], interpolation='None')
    plt.colorbar(orientation='horizontal')
    plt.title('z-slice')

    plt.show()


if __name__ == '__main__':
    import sys
    examples = {
        'box': example_box,
        'cube': example_cube,
    }
    if len(sys.argv) != 2 or sys.argv[1] not in examples:
        print("Run as")
        print("  [python] {} <example>".format("validate_3d_simulation"))
        print("")
        print("  <example> being one of:")
        for f in examples.keys():
            print("    " + f)
    else:
        examples[sys.argv[1]]()
