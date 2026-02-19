import marimo

__generated_with = '0.19.11'
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    from pathlib import Path

    import matplotlib.pyplot as plt
    import numpy as np

    from gaussianfft.util import (
        PaddingAnalyzer,
        PaddingAnalyzerDefaults,
    )

    return PaddingAnalyzer, PaddingAnalyzerDefaults, Path, np, plt


@app.cell
def _(Path):
    storage_area = Path(__file__).parent / 'data'
    storage_area.mkdir(exist_ok=True, parents=True)
    return (storage_area,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This notebook compares the estimated variograms and how the error/deviation
    from the true variogram looks at different distances.
    For each variogram type, three sets of plots are generated:
    low range-to-grid-size ratio,
    range-to-grid-size aprx 1.0,
    and high range-to-grid-size ratio.
    Ideally,
    it is possible to derive a method for choosing the padding that only depends on the range and variogram type.

    The following limitations must be considered:
    - It is assumed that the variogram estimation has converged
    - The variogram is estimated from the point (0, 0, 0), only
    - The analysis is independent of L (grid size) and n (number of grid cells)
    - The analysis is performed only for a cube and an isotropic variogram
    """)
    return


@app.cell
def _(PaddingAnalyzer, plt):
    def plot5(r: PaddingAnalyzer, vmin=-0.25, vmax=0.25):
        plt.rcParams['figure.figsize'] = [20, 6 * len(r.range)]
        for ir in range(len(r.range)):
            plt.subplot(100 * len(r.range) + 10 + 1 * ir + 1)
            plt.title(r.range[ir])
            plt.contourf(
                r.grid,
                r.padding_f,
                r.deltas[:, ir, :],
                40,
                vmin=vmin,
                vmax=vmax,
                cmap='bwr',
            )
            plt.colorbar()
            plt.show()

    return (plot5,)


@app.cell
def _(np):
    # Range definitions (original setup)
    low_range = np.linspace(0.05, 0.45, 9)
    equal_range = np.linspace(0.8, 1.2, 5)
    high_range = np.linspace(2, 10, 9)

    return equal_range, high_range, low_range


@app.cell
def _(np):
    # Range definitions (optional setup with less padding)
    padding_1 = np.linspace(0, 2.5, 11)
    return (padding_1,)


@app.cell
def _(PaddingAnalyzerDefaults):
    PaddingAnalyzerDefaults.nmax = 6000
    PaddingAnalyzerDefaults.seed = 1333
    PaddingAnalyzerDefaults.ndims = 1
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Dimension == 1
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Spherical
    """)
    return


@app.cell
def _(PaddingAnalyzer, low_range, np, padding_1, plot5, storage_area):
    _rpa_short = PaddingAnalyzer(low_range, padding_1, vtype='spherical')
    np.savez(
        storage_area / 'spherical_short.npz',
        grid=_rpa_short.grid,
        range=_rpa_short.range,
        padding_f=_rpa_short.padding_f,
    )
    plot5(_rpa_short)
    return


@app.cell
def _(PaddingAnalyzer, equal_range, np, padding_1, plot5, storage_area):
    _rpa_equal = PaddingAnalyzer(equal_range, padding_1, vtype='spherical')
    np.savez(
        storage_area / 'spherical_equal.npz',
        grid=_rpa_equal.grid,
        range=_rpa_equal.range,
        padding_f=_rpa_equal.padding_f,
    )
    plot5(_rpa_equal)
    return


@app.cell
def _(PaddingAnalyzer, high_range, np, padding_1, plot5, storage_area):
    _rpa_high = PaddingAnalyzer(high_range, padding_1, vtype='spherical')
    np.savez(
        storage_area / 'spherical_high.npz',
        grid=_rpa_high.grid,
        range=_rpa_high.range,
        padding_f=_rpa_high.padding_f,
    )
    plot5(_rpa_high)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Gaussian
    """)
    return


@app.cell
def _(PaddingAnalyzerDefaults):
    PaddingAnalyzerDefaults.nmax = 5000
    return


@app.cell
def _(PaddingAnalyzer, low_range, np, padding_1, plot5, storage_area):
    _rpa_short = PaddingAnalyzer(low_range, padding_1, vtype='gaussian')
    np.savez(
        storage_area / 'gaussian_short.npz',
        grid=_rpa_short.grid,
        range=_rpa_short.range,
        padding_f=_rpa_short.padding_f,
    )
    plot5(_rpa_short)
    return


@app.cell
def _(PaddingAnalyzer, equal_range, np, padding_1, plot5, storage_area):
    _rpa_equal = PaddingAnalyzer(equal_range, padding_1, vtype='gaussian')
    np.savez(
        storage_area / 'gaussian_equal.npz',
        grid=_rpa_equal.grid,
        range=_rpa_equal.range,
        padding_f=_rpa_equal.padding_f,
    )
    plot5(_rpa_equal)
    return


@app.cell
def _(PaddingAnalyzer, high_range, np, padding_1, plot5, storage_area):
    _rpa_high = PaddingAnalyzer(high_range, padding_1, vtype='gaussian')
    np.savez(
        storage_area / 'gaussian_high.npz',
        grid=_rpa_high.grid,
        range=_rpa_high.range,
        padding_f=_rpa_high.padding_f,
    )
    plot5(_rpa_high)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Dimension == 2

    This is time consuming. It may help to only look at shorter padding
    """)
    return


@app.cell
def _(PaddingAnalyzerDefaults):
    PaddingAnalyzerDefaults.ndims = 2
    return


@app.cell
def _(
    PaddingAnalyzer,
    PaddingAnalyzerDefaults,
    equal_range,
    np,
    padding_1,
    plot5,
    storage_area,
):
    PaddingAnalyzerDefaults.nmax = 6000
    _rpa_equal = PaddingAnalyzer(equal_range, padding_1, vtype='spherical')
    np.savez(
        storage_area / 'spherical_equal.npz',
        grid=_rpa_equal.grid,
        range=_rpa_equal.range,
        padding_f=_rpa_equal.padding_f,
    )
    plot5(_rpa_equal)
    return


if __name__ == '__main__':
    app.run()
