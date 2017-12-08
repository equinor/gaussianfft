import numpy as np
import matplotlib.pyplot as plt
import nrlib


def example_cube():
    nrlib.seed(123)
    n = 200
    p = 800
    d = 0.5
    variogram = nrlib.variogram('gaussian', main_range=100, perp_range=100)
    field = nrlib.advanced.simulate(variogram, n, d, n, d, padx=p, pady=p)
    field2d = np.array(field).reshape((n, n), order='F')
    plot_surface(field2d, 'Gaussian variogram, insufficient simulation padding')
    plt.show()


def example_cubes():
    n = 100
    d = 1.0
    for i, p in enumerate([100, 200, 300, 400]):
        nrlib.seed(123)
        variogram = nrlib.variogram('gaussian', main_range=100, perp_range=100)
        field = nrlib.advanced.simulate(variogram, n, d, n, d, padx=p, pady=p)
        field2d = np.array(field).reshape((n, n), order='F')
        plt.subplot(411 + i)
        plot_surface(field2d, 'Gaussian variogram, padding={} x range'.format(int(p/100)))
    plt.show()


def example_box():
    nrlib.seed(123)
    variogram = nrlib.variogram('exponential', main_range=1000.0, perp_range=1000.0,)
    nx, ny = 50, 100
    dx, dy = 10, 10
    field = nrlib.simulate(variogram, nx, dx, ny, dy)
    field2d = np.array(field).reshape((nx, ny), order='F')
    plot_surface(field2d, 'Exponential variogram')
    plt.show()


def plot_surface(field, title):
    plt.imshow(field, interpolation='None')
    plt.title(title)


if __name__ == '__main__':
    import sys
    examples = {
        'box': example_box,
        'cube': example_cube,
        'cubes': example_cubes,
    }
    if len(sys.argv) != 2 or sys.argv[1] not in examples:
        print("Run as")
        print("  [python] {} <example>".format("validate_2d_simulation"))
        print("")
        print("  <example> being one of:")
        for f in examples.keys():
            print("    " + f)
    else:
        examples[sys.argv[1]]()
