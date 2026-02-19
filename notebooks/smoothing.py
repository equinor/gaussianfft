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

    # '%matplotlib inline' command supported automatically in marimo
    plt.rcParams['figure.figsize'] = [10, 7]
    import os

    os.getpid()
    return gaussianfft, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Verification that the code works
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    gaussianfft.seed(123)
    _v = gaussianfft.variogram('gaussian', 1000.0, 1000.0)
    _f1 = np.array(gaussianfft.advanced.simulate(_v, 100, 10.0, 100, 10.0)).reshape((100, 100), order='F')
    plt.imshow(_f1)
    return


@app.cell
def _(gaussianfft, np, plt):
    gaussianfft.seed(123)
    _v = gaussianfft.variogram('gaussian', 1000.0, 1000.0)
    _f1 = np.array(gaussianfft.advanced.simulate(_v, 100, 10.0, 100, 10.0, sx=0.05, sy=0.05)).reshape(
        (100, 100), order='F'
    )
    plt.imshow(_f1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # A Case That Breaks
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    gaussianfft.seed(123)
    _v = gaussianfft.variogram('gaussian', 1000.0, 1000.0)
    f3 = np.array(gaussianfft.advanced.simulate(_v, 100, 10.0, 100, 10.0, padx=200, pady=200)).reshape(
        (100, 100), order='F'
    )
    plt.imshow(f3)
    return


@app.cell
def _(gaussianfft, np, plt):
    gaussianfft.seed(123)
    _v = gaussianfft.variogram('gaussian', 1000.0, 1000.0)
    f4 = np.array(
        gaussianfft.advanced.simulate(_v, 100, 10.0, 100, 10.0, padx=200, pady=200, sx=0.15, sy=0.15)
    ).reshape((100, 100), order='F')
    plt.imshow(f4)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### single direction smoothing
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    gaussianfft.seed(123)
    _v = gaussianfft.variogram('gaussian', 1000.0, 1000.0)
    _f5 = np.array(gaussianfft.advanced.simulate(_v, 100, 10.0, 100, 10.0, padx=200, pady=200, sx=0.15)).reshape(
        (100, 100), order='F'
    )
    plt.imshow(_f5)
    return


@app.cell
def _(gaussianfft, np, plt):
    gaussianfft.seed(123)
    _v = gaussianfft.variogram('gaussian', 1000.0, 1000.0)
    _f5 = np.array(gaussianfft.advanced.simulate(_v, 100, 10.0, 100, 10.0, padx=200, pady=200, sy=0.15)).reshape(
        (100, 100), order='F'
    )
    plt.imshow(_f5)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## So far...

    The smoothing can have the desired effect (reduce necessary padding),
    but the question is at what cost? Moreover, is the implementation correct when introducing anisotropy:

    Hence, the following are stated as questions to be answered
    - Does it have the desired effect for other variograms?
    - Does it work as intended for anisotropy?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Testing Anisotropy
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Different direction; different smoothing
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    gaussianfft.seed(123)
    _v = gaussianfft.variogram('gaussian', 1000.0, 100.0)
    _f6 = np.array(gaussianfft.advanced.simulate(_v, 100, 10.0, 100, 10.0, padx=100, pady=10)).reshape(
        (100, 100), order='F'
    )
    plt.imshow(_f6)
    return


@app.cell
def _(gaussianfft, np, plt):
    gaussianfft.seed(123)
    _v = gaussianfft.variogram('gaussian', 1000.0, 100.0)
    f7 = np.array(
        gaussianfft.advanced.simulate(_v, 100, 10.0, 100, 10.0, padx=100, pady=10, sx=0.05, sy=0.05)
    ).reshape((100, 100), order='F')
    plt.imshow(f7)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Above, grid size and padding is $2 \cdot range$.
    This is known to be insufficient for a Gaussian variogram.
    Applying smoothing in both directions helps, but the striping effect is still there.
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    gaussianfft.seed(123)
    _v = gaussianfft.variogram('gaussian', 1000.0, 100.0, azimuth=45.0)
    _f6 = np.array(gaussianfft.advanced.simulate(_v, 100, 10.0, 100, 10.0, padx=100, pady=100)).reshape(
        (100, 100), order='F'
    )
    plt.imshow(_f6)
    return


@app.cell
def _(gaussianfft, np, plt):
    gaussianfft.seed(123)
    _v = gaussianfft.variogram('gaussian', 1000.0, 100.0, azimuth=45.0)
    _f6 = np.array(
        gaussianfft.advanced.simulate(_v, 100, 10.0, 100, 10.0, padx=100, pady=100, sx=0.5, sy=0.5)
    ).reshape((100, 100), order='F')
    plt.imshow(_f6)
    return


@app.cell
def _(gaussianfft, np, plt):
    gaussianfft.seed(123)
    _v = gaussianfft.variogram('gaussian', 1000.0, 100.0, azimuth=45.0)
    _f6 = np.array(
        gaussianfft.advanced.simulate(_v, 100, 10.0, 100, 10.0, padx=100, pady=100, sx=0.05, sy=0.05)
    ).reshape((100, 100), order='F')
    plt.imshow(_f6)
    return


if __name__ == '__main__':
    app.run()
