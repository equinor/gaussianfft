import numpy as np
import matplotlib.pyplot as plt
import nrlib


def example_cube():
    nrlib.seed(123)
    variogram = nrlib.variogram('exponential', main_range=1000.0, perp_range=1000.0,)
    nx, ny = 100, 100
    dx, dy = 10, 10
    field = nrlib.simulate(variogram, nx, dx, ny, dy)
    field2d = np.array(field).reshape((nx, ny), order='F')
    plot_surface(field2d)


def example_box():
    nrlib.seed(123)
    variogram = nrlib.variogram('exponential', main_range=1000.0, perp_range=1000.0,)
    nx, ny = 50, 100
    dx, dy = 10, 10
    field = nrlib.simulate(variogram, nx, dx, ny, dy)
    field2d = np.array(field).reshape((nx, ny), order='F')
    plot_surface(field2d)


def plot_surface(field):
    plt.imshow(field, interpolation='None')
    plt.colorbar(orientation='horizontal')
    plt.title('x-slice')
    plt.show()


if __name__ == '__main__':
    import sys
    examples = {
        'box': example_box,
        'cube': example_cube,
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
