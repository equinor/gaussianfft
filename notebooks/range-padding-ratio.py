import marimo

__generated_with = '0.19.11'
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import matplotlib.pyplot as plt
    import numpy as np

    import gaussianfft
    from gaussianfft.util import EmpiricalVariogram

    plt.rcParams['figure.figsize'] = [15, 7]
    return EmpiricalVariogram, gaussianfft, np, plt


@app.cell
def _(np, range_length_ratio):
    def filter_deltas(m, d):
        deltas_nan = np.array(d)  # Filter nans
        nan_cols = np.any(np.isnan(deltas_nan), axis=0)
        deltas_nan = deltas_nan[:, np.invert(nan_cols)]
        mid_nan = m[np.invert(nan_cols)]
        return (mid_nan, deltas_nan, nan_cols)

    def plot_deltas(fig, ax, m, d):
        mid_nan, deltas_nan, _ = filter_deltas(m, d)
        mid_nan = mid_nan / np.max(mid_nan)
        cf = ax.contourf(
            mid_nan,
            range_length_ratio,
            deltas_nan,
            30,
            vmin=-0.15,
            vmax=0.15,
            cmap='bwr',
        )
        return cf  # Plot

    return filter_deltas, plot_deltas


@app.cell
def _(EmpiricalVariogram, gaussianfft, np):
    # Setup
    nx, ny, nz = 100, 1, 1
    dx, dy, dz = 20, 20, 20
    px, py, pz = nx, ny, nz
    dr = 0.5 * dx
    nmax = 10000
    strategy = 'origo'
    range_length_ratio = np.linspace(0.1, 2, 10)

    # Derived constants
    Lx, Ly, Lz = nx * dx, ny * dy, nz * dz

    def simulate(vtype):
        # Simulation

        deltas = [[], []]
        true_variogram = []
        estimated_variograms = [[], []]
        for r in range_length_ratio:
            v = gaussianfft.variogram(vtype, Lx * r, Ly * r, Lz * r)
            ev = EmpiricalVariogram(v, nx, dx, ny, dy, nz, dz, px, py, pz)
            true_variogram.append(ev.true_variogram(dr))
            refs = ev.pick_reference_points(strategy)
            for dd, ee in zip(deltas, estimated_variograms):
                mid, estimated_variogram, _, _, convrg = ev.estimate_variogram(nmax, dr, refs, analyze_convergence=10)
                ee.append(estimated_variogram)
                dd.append(convrg.deltas[-1])
            # TODO: analyze convergence
        return mid, deltas, true_variogram, estimated_variograms

    return Lx, dx, nx, px, range_length_ratio, simulate


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Gaussian
    """)
    return


@app.cell
def _(simulate):
    variogram_type = 'gaussian'
    mid, deltas, tcorr, ecorr = simulate(variogram_type)
    return deltas, ecorr, mid, tcorr, variogram_type


@app.cell
def _(deltas, mid, plot_deltas, plt):
    # Plot comparison
    _fig, _axes = plt.subplots(nrows=1, ncols=2)
    _c = plot_deltas(_fig, _axes[0], mid, deltas[0])
    _c = plot_deltas(_fig, _axes[1], mid, deltas[1])
    _axes[0].set_ylabel('range/length ratio')
    _axes[0].set_xlabel('correlation range')
    _axes[1].set_xlabel('correlation range')
    _fig.colorbar(_c, ax=_axes.ravel().tolist())
    return


@app.cell
def _(deltas, ecorr, filter_deltas, mid, np, plt, range_length_ratio, tcorr):
    # Inspect variogram estimation
    idelta = 0
    ratio = 0.75

    fmid, fdelta, nancols = filter_deltas(mid, deltas[idelta])
    ir = np.argmin(np.abs(range_length_ratio - ratio))
    evario = np.array(ecorr[idelta][ir])[np.invert(nancols)]
    tvario = np.array(tcorr[ir])

    plt.plot(fmid, evario)
    plt.plot(tvario[0], tvario[1])
    # plt.plot(fmid, fdelta[ir, :])
    return (ratio,)


@app.cell
def _(Lx, dx, gaussianfft, nx, plt, px, ratio, variogram_type):
    # Show a realization
    v = gaussianfft.variogram(variogram_type, ratio * Lx)
    f = gaussianfft.advanced.simulate(v, nx, dx, padx=px)
    plt.plot(f)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Spherical
    """)
    return


@app.cell
def _(simulate):
    variogram_type_1 = 'spherical'
    mid_1, deltas_1, tcorr_1, ecorr_1 = simulate(variogram_type_1)
    return deltas_1, mid_1


@app.cell
def _(deltas_1, mid_1, plot_deltas, plt):
    _fig, _axes = plt.subplots(nrows=1, ncols=2)
    _c = plot_deltas(_fig, _axes[0], mid_1, deltas_1[0])
    _c = plot_deltas(_fig, _axes[1], mid_1, deltas_1[1])
    _axes[0].set_ylabel('range/length ratio')
    _axes[0].set_xlabel('correlation range')
    _axes[1].set_xlabel('correlation range')
    _fig.colorbar(_c, ax=_axes.ravel().tolist())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Exponential
    """)
    return


@app.cell
def _(simulate):
    variogram_type_2 = 'exponential'
    mid_2, deltas_2, tcorr_2, ecorr_2 = simulate(variogram_type_2)
    return deltas_2, mid_2


@app.cell
def _(deltas_2, mid_2, plot_deltas, plt):
    _fig, _axes = plt.subplots(nrows=1, ncols=2)
    _c = plot_deltas(_fig, _axes[0], mid_2, deltas_2[0])
    _c = plot_deltas(_fig, _axes[1], mid_2, deltas_2[1])
    _axes[0].set_ylabel('range/length ratio')
    _axes[0].set_xlabel('correlation range')
    _axes[1].set_xlabel('correlation range')
    _fig.colorbar(_c, ax=_axes.ravel().tolist())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Matern52
    """)
    return


@app.cell
def _(simulate):
    variogram_type_3 = 'matern52'
    mid_3, deltas_3, tcorr_3, ecorr_3 = simulate(variogram_type_3)
    return deltas_3, mid_3


@app.cell
def _(deltas_3, mid_3, plot_deltas, plt):
    _fig, _axes = plt.subplots(nrows=1, ncols=2)
    _c = plot_deltas(_fig, _axes[0], mid_3, deltas_3[0])
    _c = plot_deltas(_fig, _axes[1], mid_3, deltas_3[1])
    _axes[0].set_ylabel('range/length ratio')
    _axes[0].set_xlabel('correlation range')
    _axes[1].set_xlabel('correlation range')
    _fig.colorbar(_c, ax=_axes.ravel().tolist())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # General Exponential (1.5)
    """)
    return


@app.cell
def _(simulate):
    variogram_type_4 = 'general_exponential'
    mid_4, deltas_4, tcorr_4, ecorr_4 = simulate(variogram_type_4)
    return deltas_4, mid_4


@app.cell
def _(deltas_4, mid_4, plot_deltas, plt):
    _fig, _axes = plt.subplots(nrows=1, ncols=2)
    _c = plot_deltas(_fig, _axes[0], mid_4, deltas_4[0])
    _c = plot_deltas(_fig, _axes[1], mid_4, deltas_4[1])
    _axes[0].set_ylabel('range/length ratio')
    _axes[0].set_xlabel('correlation range')
    _axes[1].set_xlabel('correlation range')
    _fig.colorbar(_c, ax=_axes.ravel().tolist())
    return


if __name__ == '__main__':
    app.run()
