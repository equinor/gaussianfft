import marimo

__generated_with = "0.19.11"
app = marimo.App()


@app.cell
def _():
    import gaussianfft
    import numpy as np
    import matplotlib.pyplot as plt
    plt.rcParams['figure.dpi'] = 300

    v = gaussianfft.variogram('general_exponential', 2000.0, 1000.0, azimuth=30.0)
    nx, ny = 100, 125
    dx, dy = 20.0, 20.0
    gaussianfft.seed(42)
    f_vector = gaussianfft.simulate(v, nx, dx, ny, dy)
    f = np.array(f_vector).reshape((nx, ny), order='F')

    x = np.arange(0, nx) * dx
    y = np.arange(0, ny) * dy
    plt.contourf(y, x, f, 30)
    plt.colorbar()
    plt.xlabel('East')
    plt.ylabel('North')
    plt.show()
    return


if __name__ == "__main__":
    app.run()
