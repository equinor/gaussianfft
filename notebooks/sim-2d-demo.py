import marimo

__generated_with = "0.19.11"
app = marimo.App()


@app.cell
def _():
    import gaussianfft
    import numpy as np
    import matplotlib.pyplot as plt
    # '%matplotlib inline' command supported automatically in marimo
    plt.rcParams['figure.figsize'] = [15, 10]
    return gaussianfft, np, plt


@app.cell
def _(gaussianfft):
    nx, ny = 100, 100
    dx, dy = 1, 1
    v = gaussianfft.variogram('general_exponential', 12, 12, power=1.5, azimuth=0)
    return dx, dy, nx, ny, v


@app.cell
def _(dx, np, nx, plt, v):
    corr = [v.corr(x) for x in np.linspace(0, nx * dx, 100)]
    plt.plot(corr)
    return


@app.cell
def _(dx, dy, gaussianfft, np, nx, ny, plt, v):
    gaussianfft.seed(423)
    _f = gaussianfft.advanced.simulate(v, nx, dx, ny, dy, padx=20, pady=20)
    _f_arr = np.array(_f).reshape((nx, ny), order='F')
    plt.imshow(_f_arr, interpolation='None')
    plt.colorbar()
    return


@app.cell
def _(dx, dy, gaussianfft, np, nx, ny, plt, v):
    gaussianfft.seed(42)
    _f = gaussianfft.advanced.simulate(v, nx, dx, ny, dy, padx=100, pady=100)
    _f_arr = np.array(_f).reshape((nx, ny), order='F')
    plt.imshow(_f_arr, interpolation='None')
    plt.colorbar()
    return


@app.cell
def _(dx, dy, gaussianfft, np, nx, ny, plt, v):
    gaussianfft.seed(42)
    _f = gaussianfft.advanced.simulate(v, nx, dx, ny, dy, padx=50, pady=50)
    _f_arr = np.array(_f).reshape((nx, ny), order='F')
    plt.imshow(_f_arr, interpolation='None')
    plt.colorbar()
    return


@app.cell
def _(dx, dy, gaussianfft, np, nx, ny, plt, v):
    gaussianfft.seed(42)
    _f = gaussianfft.advanced.simulate(v, nx, dx, ny, dy, padx=75, pady=75)
    _f_arr = np.array(_f).reshape((nx, ny), order='F')
    plt.imshow(_f_arr, interpolation='None')
    plt.colorbar()
    return


@app.cell
def _(dx, dy, gaussianfft, np, nx, ny, plt, v):
    gaussianfft.seed(42)
    _f = gaussianfft.advanced.simulate(v, nx, dx, ny, dy, padx=100, pady=100)
    _f_arr = np.array(_f).reshape((nx, ny), order='F')
    plt.imshow(_f_arr, interpolation='None')
    plt.colorbar()
    return


if __name__ == "__main__":
    app.run()
