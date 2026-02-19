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
    plt.rcParams['figure.figsize'] = [10.0, 7.0]  # notebook
    return gaussianfft, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Basic plot
    """)
    return


@app.cell
def _(gaussianfft, np):
    _v = gaussianfft.variogram('gaussian', 1000.0, 250.0, azimuth=30)
    nx, ny = (750, 1000)
    dx, dy = (10, 10)
    _field = gaussianfft.simulate(_v, nx, dx, ny, dy)
    field_array = np.array(_field).reshape((nx, ny), order='F')
    return dx, dy, field_array, nx, ny


@app.cell
def _(dx, dy, field_array, np, nx, ny, plt):
    plt.contourf(np.arange(0, nx) * dx,
                 np.arange(0, ny) * dy,
                 field_array.T,
                 40)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Variogram comparisons
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    vtypes = ['exponential', 'spherical', 'gaussian', 'matern32', 'matern52', 'matern72', 'general_exponential']
    fields = {}
    nx_1, ny_1 = (1500, 2000)
    dx_1, dy_1 = (10, 10)
    for _t in vtypes:
        gaussianfft.seed(123)
        vario = gaussianfft.variogram(_t, 1000.0, 500.0, azimuth=30, power=1.5)
        fields[_t] = np.array(gaussianfft.simulate(vario, nx_1, dx_1, ny_1, dy_1)).reshape((nx_1, ny_1), order='F')
    shown_variograms = vtypes
    fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(15, 10))
    global_min = min((_field.min() for _field in fields.values()))
    global_max = max((_field.max() for _field in fields.values()))
    axes_flat = axes.flat
    for _t, ax in zip(shown_variograms, axes_flat):
        im = ax.imshow(fields[_t][700:800, 950:1050], interpolation='None', vmin=global_min, vmax=global_max)
        ax.set_title(_t)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='5%', pad=0.08)
        plt.colorbar(im, cax=cax)
    axes_flat[7].axis('off')
    axes_flat[8].axis('off')
    fig.tight_layout()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Azimuth verification
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    azimuth_fields = []
    angles = [0, 30, 60, 90, 120, 150]
    for _a in angles:
        gaussianfft.seed(1231312)
        _v = gaussianfft.variogram('gaussian', 1000.0, 250.0, azimuth=_a)
        nx_2, ny_2 = (750, 1000)
        dx_2, dy_2 = (10, 10)
        _field = gaussianfft.simulate(_v, nx_2, dx_2, ny_2, dy_2)
        field_array_1 = np.array(_field).reshape((nx_2, ny_2), order='F')
        azimuth_fields.append(field_array_1)
    _subplots = [231, 232, 233, 234, 235, 236]
    for _t, _s, _a in zip(azimuth_fields, _subplots, angles):
        plt.subplot(_s)
        plt.contourf(np.arange(0, nx_2) * dx_2, np.arange(0, ny_2) * dy_2, _t.T, 40)
        plt.title('azimuth=' + str(_a))
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Experimental padding (Advanced)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2D
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    padding_fields = []
    padding_fraction = [0.01, 0.1, 0.2, 0.5, 0.8, 1.0]
    _v = gaussianfft.variogram('spherical', 2000.0, 2000.0)
    nx_3, ny_3 = (300, 500)
    dx_3, dy_3 = (20, 20)
    for _f in padding_fraction:
        gaussianfft.seed(1231312)
        _field = gaussianfft.advanced.simulate(_v, nx_3, dx_3, ny_3, dy_3, padx=int(nx_3 * _f), pady=int(ny_3 * _f))
        field_array_2 = np.array(_field).reshape((nx_3, ny_3), order='F')
        padding_fields.append(field_array_2)
    _subplots = [231, 232, 233, 234, 235, 236]
    for _t, _s, _a in zip(padding_fields, _subplots, padding_fraction):
        _t = np.roll(_t, int(nx_3 / 2), axis=0)
        plt.subplot(_s)
        plt.contourf(np.arange(0, nx_3) * dx_3, np.arange(0, ny_3) * dy_3, _t.T, 40)
        plt.title('fraction=' + str(_a))
    plt.show()
    return nx_3, padding_fields, padding_fraction


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Inspect differences when rolling
    """)
    return


@app.cell
def _(np, nx_3, padding_fields, padding_fraction, plt):
    _subplots = [231, 232, 233, 234, 235, 236]
    for _t, _s, _a in zip(padding_fields, _subplots, padding_fraction):
        _t = np.roll(_t, int(nx_3 / 2), axis=0)
        _t = np.abs(np.diff(_t, axis=0))
        plt.subplot(_s)
        plt.plot(_t[int(nx_3 / 2), :])
        plt.plot(_t[int(nx_3 / 2) - 1, :])
        plt.title('fraction=' + str(_a))
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1D
    """)
    return


@app.cell
def _(gaussianfft, np):
    padding_fields_1 = []
    padding_fraction_1 = [0.01, 0.1, 0.2, 0.5, 0.8, 1.0]
    _v = gaussianfft.variogram('spherical', 1000.0)
    nx_4 = 300
    dx_4 = 20
    for _f in padding_fraction_1:
        gaussianfft.seed(1231312)
        _field = gaussianfft.advanced.simulate(_v, nx_4, dx_4, padx=int(nx_4 * _f))
        field_array_3 = np.array(_field)
        padding_fields_1.append(field_array_3)
    return dx_4, nx_4, padding_fields_1, padding_fraction_1


@app.cell
def _(dx_4, np, nx_4, padding_fields_1, padding_fraction_1, plt):
    _subplots = [231, 232, 233, 234, 235, 236]
    for _t, _s, _a in zip(padding_fields_1, _subplots, padding_fraction_1):
        _t = np.roll(_t, int(nx_4 / 2))
        plt.subplot(_s)
        plt.plot(np.arange(0, nx_4) * dx_4, _t / np.max(_t))
        plt.plot(np.arange(0, nx_4 - 1) * dx_4, np.diff(_t) / np.max(np.diff(_t)))
        plt.title('fraction=' + str(_a))
    plt.show()
    return


if __name__ == "__main__":
    app.run()
