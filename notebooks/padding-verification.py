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
def _(dx, dy, gaussianfft, np, nx, ny, plt, px, py, v):
    def run_and_plot_simulation():
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
def _(dx, dy, dz, gaussianfft, np, nx, ny, nz, plt, px, py, pz, v):
    def run_and_plot_simulation3d():
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
    rx, ry = 1000.0, 1000.0
    v = gaussianfft.variogram('gaussian', rx, ry)
    nx, ny = 100, 100
    dx, dy = 20, 20
    px = find_padding(nx, dx, rx)
    py = find_padding(ny, dy, ry)

    run_and_plot_simulation()

    px = int(find_padding(nx, dx, rx)/2)
    py = int(find_padding(ny, dy, ry)/2)
    run_and_plot_simulation()

    px = int(find_padding(nx, dx, rx)/4)
    py = int(find_padding(ny, dy, ry)/4)
    run_and_plot_simulation()
    return dx, dy, nx, ny, px, py, v


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Spherical, 2D

    Spherical is kind of special since the factor 3 above can be replace by 2
    """)
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation):
    rx_1, ry_1 = (1000.0, 1000.0)
    v_1 = gaussianfft.variogram('spherical', rx_1, ry_1)
    nx_1, ny_1 = (100, 100)
    dx_1, dy_1 = (20, 20)
    px_1 = find_padding(nx_1, dx_1, rx_1)
    py_1 = find_padding(ny_1, dy_1, ry_1)
    run_and_plot_simulation()
    px_1 = int(find_padding(nx_1, dx_1, rx_1) / 2)
    py_1 = int(find_padding(ny_1, dy_1, ry_1) / 2)
    run_and_plot_simulation()
    px_1 = int(find_padding(nx_1, dx_1, rx_1) / 4)
    py_1 = int(find_padding(ny_1, dy_1, ry_1) / 4)
    run_and_plot_simulation()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Gaussian, 2D, diverse range
    """)
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation):
    rx_2, ry_2 = (1000.0, 250.0)
    v_2 = gaussianfft.variogram('spherical', rx_2, ry_2)
    nx_2, ny_2 = (100, 100)
    dx_2, dy_2 = (20, 20)
    px_2 = find_padding(nx_2, dx_2, rx_2)
    py_2 = find_padding(ny_2, dy_2, ry_2)
    px_2 = max(px_2, py_2)
    py_2 = px_2
    run_and_plot_simulation()
    px_2 = find_padding(nx_2, dx_2, rx_2)
    py_2 = find_padding(ny_2, dy_2, ry_2)
    run_and_plot_simulation()
    px_2 = int(find_padding(nx_2, dx_2, rx_2) / 2)
    py_2 = int(find_padding(ny_2, dy_2, ry_2) / 2)
    run_and_plot_simulation()
    px_2 = int(find_padding(nx_2, dx_2, rx_2) / 4)
    py_2 = int(find_padding(ny_2, dy_2, ry_2) / 4)
    run_and_plot_simulation()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Gaussian, 2D, azimuth
    """)
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation):
    rx_3, ry_3 = (1000.0, 250.0)
    v_3 = gaussianfft.variogram('gaussian', rx_3, ry_3, azimuth=45)
    nx_3, ny_3 = (100, 100)
    dx_3, dy_3 = (20, 20)
    px_3 = find_padding(nx_3, dx_3, rx_3)
    py_3 = find_padding(ny_3, dy_3, ry_3)
    px_3 = max(px_3, py_3)
    py_3 = px_3
    run_and_plot_simulation()
    px_3 = find_padding(nx_3, dx_3, rx_3)
    py_3 = find_padding(ny_3, dy_3, ry_3)
    run_and_plot_simulation()
    px_3 = int(find_padding(nx_3, dx_3, rx_3) / 2)
    py_3 = int(find_padding(ny_3, dy_3, ry_3) / 2)
    run_and_plot_simulation()
    px_3 = int(find_padding(nx_3, dx_3, rx_3) / 4)
    py_3 = int(find_padding(ny_3, dy_3, ry_3) / 4)
    run_and_plot_simulation()
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation):
    rx_4, ry_4 = (1000.0, 250.0)
    v_4 = gaussianfft.variogram('gaussian', rx_4, ry_4, azimuth=90)
    nx_4, ny_4 = (100, 100)
    dx_4, dy_4 = (20, 20)
    px_4 = find_padding(nx_4, dx_4, rx_4)
    py_4 = find_padding(ny_4, dy_4, ry_4)
    px_4 = max(px_4, py_4)
    py_4 = px_4
    run_and_plot_simulation()
    px_4 = find_padding(nx_4, dx_4, rx_4)
    py_4 = find_padding(ny_4, dy_4, ry_4)
    run_and_plot_simulation()
    px_4 = int(find_padding(nx_4, dx_4, rx_4) / 2)
    py_4 = int(find_padding(ny_4, dy_4, ry_4) / 2)
    run_and_plot_simulation()
    px_4 = int(find_padding(nx_4, dx_4, rx_4) / 4)
    py_4 = int(find_padding(ny_4, dy_4, ry_4) / 4)
    run_and_plot_simulation()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Matern32, 2D, azimuth
    """)
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation):
    rx_5, ry_5 = (1000.0, 250.0)
    v_5 = gaussianfft.variogram('matern32', rx_5, ry_5, azimuth=135)
    nx_5, ny_5 = (150, 100)
    dx_5, dy_5 = (20, 20)
    px_5 = find_padding(nx_5, dx_5, rx_5)
    py_5 = find_padding(ny_5, dy_5, ry_5)
    px_5 = max(px_5, py_5)
    py_5 = px_5
    run_and_plot_simulation()
    px_5 = find_padding(nx_5, dx_5, rx_5)
    py_5 = find_padding(ny_5, dy_5, ry_5)
    run_and_plot_simulation()
    px_5 = int(find_padding(nx_5, dx_5, rx_5) / 2)
    py_5 = int(find_padding(ny_5, dy_5, ry_5) / 2)
    run_and_plot_simulation()
    px_5 = int(find_padding(nx_5, dx_5, rx_5) / 4)
    py_5 = int(find_padding(ny_5, dy_5, ry_5) / 4)
    run_and_plot_simulation()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Matern32, 3D, azimuth, dip
    """)
    return


@app.cell
def _(gaussianfft, run_and_plot_simulation3d):
    rx_6, ry_6, rz = (1000.0, 500.0, 250.0)
    v_6 = gaussianfft.variogram('matern32', rx_6, ry_6, rz, azimuth=135, dip=30)
    nx_6, ny_6, nz = (150, 100, 50)
    dx_6, dy_6, dz = (20, 20, 40)
    px_6 = find_padding(nx_6, dx_6, rx_6)
    py_6 = find_padding(ny_6, dy_6, ry_6)
    pz = find_padding(nz, dz, rz)
    run_and_plot_simulation3d()
    return dx_6, dy_6, dz, nx_6, ny_6, nz, pz, rx_6, ry_6, rz


@app.cell
def _(
    dx_6,
    dy_6,
    dz,
    nx_6,
    ny_6,
    nz,
    run_and_plot_simulation3d,
    rx_6,
    ry_6,
    rz,
):
    px_7 = int(find_padding(nx_6, dx_6, rx_6) / 8)
    py_7 = int(find_padding(ny_6, dy_6, ry_6) / 8)
    pz_1 = int(find_padding(nz, dz, rz) / 8)
    run_and_plot_simulation3d()
    return


if __name__ == "__main__":
    app.run()
