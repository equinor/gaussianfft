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
    # '%matplotlib inline' command supported automatically in marimo
    plt.rcParams['figure.figsize'] = [10, 7]
    return gaussianfft, np, plt


@app.cell
def _(gaussianfft, np, plt):
    _v = gaussianfft.variogram('gaussian', 1.0, power=1.999)
    L = 0.5
    X = np.linspace(0, L / 2, 65)
    c_list = [_v.corr(L / 2 - x) for x in X]
    c = np.array(c_list)
    c_flat = np.array([_v.corr(x) for x in X])
    s_pre = np.outer(np.ones((c_flat.size,)), c_flat)
    for i in range(s_pre.shape[0]):
        s_pre[i] = np.roll(s_pre[i], i)
        s_pre[i, :i] = 0
    s = s_pre + s_pre.T - np.diag(np.diag(s_pre))
    plt.imshow(s)
    plt.colorbar()
    return X, s


@app.cell
def _(np, plt, s):
    eigs = np.linalg.eig(s)[0]
    reigs = np.real(eigs)
    ieigs = np.imag(eigs)

    assert np.max(np.abs(ieigs)) < 1e-14  # Just to be sure

    print("Smallest eigvalue: {}".format(np.min(reigs)))
    print("Largest eigvalue : {}".format(np.max(reigs)))


    plt.semilogy(reigs)
    return


@app.cell
def _(np, plt, s):
    L_1 = np.linalg.cholesky(s)
    plt.imshow(L_1, interpolation='None', cmap=plt.cm.hot_r)
    plt.colorbar()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Alternative matrix decomposition

    Relevant mostly for the Gaussian variogram
    """)
    return


@app.cell
def _(np, plt, s):
    lambd, _v = np.linalg.eig(s)
    L_2 = _v * np.sqrt(lambd)
    plt.imshow(np.abs(np.real(L_2)), interpolation='None', cmap=plt.cm.hot_r)
    plt.colorbar()
    plt.show()
    plt.imshow(np.imag(L_2), interpolation='None', cmap=plt.cm.hot_r)
    plt.colorbar()
    return (L_2,)


@app.cell
def _(L_2, np, plt):
    q, r = np.linalg.qr(np.real(L_2))
    plt.imshow(r, interpolation='None', cmap=plt.cm.hot_r)
    plt.colorbar()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Factorization-based simulation
    """)
    return


@app.cell
def _(L_2, X, np):
    z = np.dot(np.real(L_2), np.random.normal(size=X.shape))
    return (z,)


@app.cell
def _(plt, z):
    plt.plot(z)
    return


if __name__ == "__main__":
    app.run()
