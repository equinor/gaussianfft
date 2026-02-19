import marimo

__generated_with = "0.19.11"
app = marimo.App()


@app.cell
def _():
    import gaussianfft
    import matplotlib.pyplot as plt
    import numpy as np
    # plt.rcParams['figure.figsize'] = [15, 10]
    return gaussianfft, np, plt


@app.cell
def _(gaussianfft):
    v = gaussianfft.variogram('exponential', 1.0)
    return (v,)


@app.cell
def _(np, v):
    x = np.linspace(0, 2.0, 100)
    corr = np.array([v.corr(d) for d in x])
    k = 0.5
    smoothing = np.exp(-0.5 * x ** 2)
    return corr, smoothing, x


@app.cell
def _(corr, plt, smoothing, x):
    plt.plot(x, corr)
    plt.plot(x, smoothing * corr)
    plt.plot(x, smoothing)
    plt.legend(['Corr', 'sCorr', 's'])
    return


@app.cell
def _(corr, np, plt, smoothing, x):
    d = 7
    plt.plot(x[:-d], np.abs(np.diff(corr, n=d)))
    plt.plot(x[:-d], np.abs(np.diff(smoothing * corr, n=d)))
    # plt.plot(x[:-d], np.diff(smoothing, n=d))
    plt.legend(['Corr', 'sCorr'])
    plt.grid()
    plt.show()
    return


@app.cell
def _(corr, np):
    np.diff(corr)
    return


@app.cell
def _(corr):
    corr
    return


if __name__ == "__main__":
    app.run()
