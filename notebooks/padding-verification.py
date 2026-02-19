import marimo

__generated_with = "0.19.11"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import gaussianfft
    import numpy as np
    import matplotlib.pyplot as plt
    plt.rcParams['figure.figsize'] = [12, 7]
    return gaussianfft, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This notebook investigates the hypothesis that $L/r > 3$ in order to generate a valid simulation result. $L$ is the length of padding + grid size and $r$ is the range of the variogram. The intention is to try different cases, set the padding according to this rule and inspect simulated realizations.
    """)
    return


@app.function
def find_padding(n, d, r):
    return int(max(3 * r/d - 1, 0))


@app.cell
def _(gaussianfft, np, plt):
    def run_and_plot_simulation(v, px, py, nx, ny, dx, dy):
        # Function that relies on data in the global scope
        gaussianfft.seed(121314)
        print('Running simulation with padding')
        print('  {} {}'.format(px, py))
        z_vec = gaussianfft.advanced.simulate(v, nx, dx, ny, dy, padx=px, pady=py)
        z = np.array(z_vec).reshape((nx, ny), order='F')

        plt.contourf(np.arange(0, nx)*dx, np.arange(0, ny)*dy, z.T, 30)
        plt.colorbar()
        plt.show()

    return (run_and_plot_simulation,)


@app.cell
def _(gaussianfft, np, plt):
    def run_and_plot_simulation3d(v, px, py, pz, nx, ny, nz, dx, dy, dz):
        # Function that relies on data in the global scope
        gaussianfft.seed(121314)
        print('Running simulation with padding')
        print('  {} {} {}'.format(px, py, pz))
        z_vec = gaussianfft.advanced.simulate(v, nx, dx, ny, dy, nz, dz, px, py, pz)
        z = np.array(z_vec).reshape((nx, ny, nz), order='F')

        plt.contourf(np.arange(0, ny)*dy, np.arange(0, nz)*dz, z[int(nx/2), :, :].T, 30)
        plt.title('YZ-slice')
        plt.colorbar()
        plt.show()

        plt.contourf(np.arange(0, nx)*dx, np.arange(0, nz)*dz, z[:, int(ny/2), :].T, 30)
        plt.title('XZ-slice')
        plt.colorbar()
        plt.show()

        plt.contourf(np.arange(0, nx)*dx, np.arange(0, ny)*dy, z[:, :, int(nz/2)].T, 30)
        plt.title('XY-slice')
        plt.colorbar()
        plt.show()

    return (run_and_plot_simulation3d,)


@app.cell
def _():
    find_padding(100, 10, 100)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Gaussian, 2D
    """)
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation):
    def _():
        rx, ry = 1000.0, 1000.0
        v = gaussianfft.variogram('gaussian', rx, ry)
        nx, ny = 100, 100
        dx, dy = 20, 20
        px = find_padding(nx, dx, rx)
        py = find_padding(ny, dy, ry)

        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)

        px = int(find_padding(nx, dx, rx)/2)
        py = int(find_padding(ny, dy, ry)/2)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)

        px = int(find_padding(nx, dx, rx)/4)
        py = int(find_padding(ny, dy, ry)/4)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)

    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Spherical, 2D

    Spherical is kind of special since the factor 3 above can be replace by 2
    """)
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation):
    def _():
        rx, ry = (1000.0, 1000.0)
        v = gaussianfft.variogram('spherical', rx, ry)
        nx, ny = (100, 100)
        dx, dy = (20, 20)
        px = find_padding(nx, dx, rx)
        py = find_padding(ny, dy, ry)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = int(find_padding(nx, dx, rx) / 2)
        py = int(find_padding(ny, dy, ry) / 2)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = int(find_padding(nx, dx, rx) / 4)
        py = int(find_padding(ny, dy, ry) / 4)
        return run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Gaussian, 2D, diverse range
    """)
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation):
    def _():
        rx, ry = (1000.0, 250.0)
        v = gaussianfft.variogram('spherical', rx, ry)
        nx, ny = (100, 100)
        dx, dy = (20, 20)
        px = find_padding(nx, dx, rx)
        py = find_padding(ny, dy, ry)
        px = max(px, py)
        py = px
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = find_padding(nx, dx, rx)
        py = find_padding(ny, dy, ry)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = int(find_padding(nx, dx, rx) / 2)
        py = int(find_padding(ny, dy, ry) / 2)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = int(find_padding(nx, dx, rx) / 4)
        py = int(find_padding(ny, dy, ry) / 4)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Gaussian, 2D, azimuth
    """)
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation):
    def _():
        rx, ry = (1000.0, 250.0)
        v = gaussianfft.variogram('gaussian', rx, ry, azimuth=45)
        nx, ny = (100, 100)
        dx, dy = (20, 20)
        px = find_padding(nx, dx, rx)
        py = find_padding(ny, dy, ry)
        px = max(px, py)
        py = px
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = find_padding(nx, dx, rx)
        py = find_padding(ny, dy, ry)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = int(find_padding(nx, dx, rx) / 2)
        py = int(find_padding(ny, dy, ry) / 2)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = int(find_padding(nx, dx, rx) / 4)
        py = int(find_padding(ny, dy, ry) / 4)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
    _()
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation):
    def _():
        rx, ry = (1000.0, 250.0)
        v = gaussianfft.variogram('gaussian', rx, ry, azimuth=90)
        nx, ny = (100, 100)
        dx, dy = (20, 20)
        px = find_padding(nx, dx, rx)
        py = find_padding(ny, dy, ry)
        px = max(px, py)
        py = px
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = find_padding(nx, dx, rx)
        py = find_padding(ny, dy, ry)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = int(find_padding(nx, dx, rx) / 2)
        py = int(find_padding(ny, dy, ry) / 2)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = int(find_padding(nx, dx, rx) / 4)
        py = int(find_padding(ny, dy, ry) / 4)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Matern32, 2D, azimuth
    """)
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation):
    def _():
        rx, ry = (1000.0, 250.0)
        v = gaussianfft.variogram('matern32', rx, ry, azimuth=135)
        nx, ny = (150, 100)
        dx, dy = (20, 20)
        px = find_padding(nx, dx, rx)
        py = find_padding(ny, dy, ry)
        px = max(px, py)
        py = px
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = find_padding(nx, dx, rx)
        py = find_padding(ny, dy, ry)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = int(find_padding(nx, dx, rx) / 2)
        py = int(find_padding(ny, dy, ry) / 2)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
        px = int(find_padding(nx, dx, rx) / 4)
        py = int(find_padding(ny, dy, ry) / 4)
        run_and_plot_simulation(v, px, py, nx, ny, dx, dy)
    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Matern32, 3D, azimuth, dip
    """)
    return


@app.cell
def _(gaussianfft):
    rx, ry, rz = (1000.0, 500.0, 250.0)
    v = gaussianfft.variogram('matern32', rx, ry, rz, azimuth=135, dip=30)
    nx, ny, nz = (150, 100, 50)
    dx, dy, dz = (20, 20, 40)
    return dx, dy, dz, nx, ny, nz, rx, ry, rz, v


@app.cell
def _(dx, dy, dz, nx, ny, nz, run_and_plot_simulation3d, rx, ry, rz, v):
    def _():
        px = find_padding(nx, dx, rx)
        py = find_padding(ny, dy, ry)
        pz = find_padding(nz, dz, rz)
        run_and_plot_simulation3d(v, px, py, pz, nx, ny, nz, dx, dy, dz)
    _()
    return


@app.cell
def _(dx, dy, dz, nx, ny, nz, run_and_plot_simulation3d, rx, ry, rz, v):
    def _():
        px = int(find_padding(nx, dx, rx) / 8)
        py = int(find_padding(ny, dy, ry) / 8)
        pz = int(find_padding(nz, dz, rz) / 8)
        run_and_plot_simulation3d(v, px, py, pz, nx, ny, nz, dx, dy, dz)
    _()
    return


if __name__ == "__main__":
    app.run()
