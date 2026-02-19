import marimo

__generated_with = "0.19.11"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import numpy as np
    import gaussianfft
    import matplotlib.pyplot as plt
    np.random.seed(123)
    # '%matplotlib inline' command supported automatically in marimo
    return gaussianfft, np, plt


@app.cell
def _(np):
    def corr_to_filter(ccc, LLL, XXX):
        dx = LLL/XXX.size
        return np.real(np.fft.ifft(np.sqrt(np.fft.fft(ccc) * dx)) / dx )

    return (corr_to_filter,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Import and utilities end
    """)
    return


@app.cell
def _(gaussianfft):
    v = gaussianfft.variogram('gaussian', 1.0)
    return (v,)


@app.cell
def _(np, v):
    L = 4.0
    X = np.linspace(0, L, 101)
    _f_sq = [v.corr(L / 2 - x) for x in X]
    f = np.sqrt(np.array(_f_sq))
    return X, f


@app.cell
def _(f, plt):
    plt.plot(f)
    return


@app.cell
def _(X, f, np, plt):
    w_spike = np.zeros((X.size * 2,))
    w_spike[X.size] = 1.0
    plt.plot(np.convolve(w_spike, f))
    return


@app.cell
def _(X, f, np, plt):
    w = np.random.normal(size=(X.size * 2,))
    plt.plot(np.convolve(w, f, 'valid'))
    return (w,)


@app.cell
def _(f, np, plt):
    f2 = (f - np.min(f))
    f2 = f2/np.max(f2)
    plt.plot(f2)
    return (f2,)


@app.cell
def _(f2, np, plt, w):
    plt.plot(np.convolve(w, f2, 'valid'))
    return


@app.cell
def _(X, f, np):
    f3 = f * np.exp(-np.square((X-np.max(X)/2.0)*2))
    return (f3,)


@app.cell
def _(f, f2, f3, plt):
    plt.plot(f3)
    plt.plot(f2)
    plt.plot(f)
    return


@app.cell
def _(f3, np, plt, w):
    plt.plot(np.convolve(w, f3, 'valid'))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Range
    """)
    return


@app.cell
def _():
    import scipy.optimize as so
    from collections import OrderedDict

    return OrderedDict, so


@app.cell
def _(OrderedDict, gaussianfft, so):
    vtypes = ['spherical', 'exponential', 'general_exponential', 'gaussian', 'matern32', 'matern52']
    powers = [1.5, 1.75, 1.99]
    alpha = 0.05
    effective_ranges = OrderedDict()

    def report_root(_vtype, root):
        effective_ranges[_vtype] = root
        print('{:30} {:.3f}'.format(_vtype, root))

    def f_root(v, alpha):
        return lambda x: v.corr(x) - alpha
    for _vtype in vtypes:
        if _vtype == 'general_exponential':
            for p in powers:
                v_1 = gaussianfft.variogram(_vtype, 1.0, power=p)
                root = so.brentq(lambda x: v_1.corr(x) - alpha, 0.0, 10.0)
                report_root(_vtype + ' - ' + str(p), root)
        else:
            v_1 = gaussianfft.variogram(_vtype, 1.0)
            root = so.brentq(lambda x: v_1.corr(x) - alpha, 0.0, 10.0)
            report_root(_vtype, root)
    return (effective_ranges,)


@app.cell
def _(effective_ranges, gaussianfft, np):
    _vtype = 'gaussian'
    v_2 = gaussianfft.variogram(_vtype, 1.0, power=1.5)
    L_1 = effective_ranges[_vtype] * 2
    X_1 = np.linspace(0, L_1, 101)
    _f_sq = [v_2.corr(L_1 / 2 - x) for x in X_1]
    f_1 = np.sqrt(np.array(_f_sq))
    return X_1, f_1


@app.cell
def _(X_1, f_1, np, plt):
    np.random.seed(121)
    w_1 = np.random.normal(size=(X_1.size * 2,))
    plt.plot(np.convolve(w_1, f_1, 'valid'))
    return


@app.cell
def _(X_1, effective_ranges, gaussianfft, np, plt):
    np.random.seed(121)
    w_2 = np.random.normal(size=(X_1.size * 2,))
    for _vtype in effective_ranges.keys():
        plt.title(_vtype)
        L_2 = effective_ranges[_vtype] * 2
        X_2 = np.linspace(0, L_2, 101)
        _power = '1.0'
        if 'general' in _vtype:
            _vtype, _power = _vtype.split(' - ')
        v_3 = gaussianfft.variogram(_vtype, 1.0, power=float(_power))
        _f_sq = [v_3.corr(L_2 / 2 - x) for x in X_2]
        f_2 = np.sqrt(np.array(_f_sq))
        plt.plot(np.convolve(w_2, f_2, 'valid'))
        plt.show()
    return (X_2,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Foreløpig konklusjon:
    Utfordringen ligger i at konvolusjonen egentlig ikke lar seg gjør på et for lite grid. Dette har ingenting med FFT å gjøre, men konvolusjonen i utgangspunktet.

    Dette betyr at løsningen må enten:
    - Lage griddet større
    - Modifisere variogrammet
    - ...
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Wrapping
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    FFT wrapper rundt. Det har innvirkning. Må sørge for at det tilfeldige feltet wrapper rundt, eller så er ikke dette en rettferdig sammenligning.
    """)
    return


@app.cell
def _(X_2, effective_ranges, gaussianfft, np, plt):
    np.random.seed(121)
    w_3 = np.random.normal(size=(X_2.size,))
    w_3 = np.hstack((w_3, w_3))
    for _vtype in effective_ranges.keys():
        plt.title(_vtype)
        L_3 = effective_ranges[_vtype] * 2
        X_3 = np.linspace(0, L_3, 101)
        _power = '1.0'
        if 'general' in _vtype:
            _vtype, _power = _vtype.split(' - ')
        v_4 = gaussianfft.variogram(_vtype, 1.0, power=float(_power))
        _f_sq = [v_4.corr(L_3 / 2 - x) for x in X_3]
        f_3 = np.sqrt(np.array(_f_sq))
        plt.plot(np.convolve(w_3, f_3, 'valid'))
        plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Take two
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Define the problem and plot the correlation kernel
    """)
    return


@app.cell
def _(gaussianfft, np):
    v_5 = gaussianfft.variogram('gaussian', 1.0)
    L_4 = 8.0
    X_4 = np.linspace(0, L_4, 1025)
    _c_list = [v_5.corr(L_4 / 2 - x) for x in X_4]
    c = np.array(_c_list)
    return L_4, X_4, c


@app.cell
def _(c, np, plt):
    plt.plot(c)
    plt.show()
    np.max(np.abs(c[::-1] - c))  # Print this to verify c is symmetric
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    For the Gaussian variogram, we have a closed for expression for a function that satisfies $f* f = c$. To verify that this function $f$ actually does satisfy this equality, we plot the convolution of the function with itself.
    """)
    return


@app.cell
def _(L_4, X_4, c, np, plt):
    # Option A:
    f_4 = np.sqrt(np.sqrt(12 / np.pi)) * np.exp(-6 * np.square(L_4 / 2 - X_4))
    plt.plot(c)
    ff_conv = L_4 / X_4.size * np.convolve(np.pad(f_4, (int(X_4.size / 2), int(X_4.size / 2)), mode='constant', constant_values=0.0), f_4, 'valid')
    plt.plot(ff_conv)
    plt.show()
    return f_4, ff_conv


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We may compare this function to the correlation function
    """)
    return


@app.cell
def _(c, f_4, plt):
    plt.plot(f_4)
    plt.plot(c)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Further, the Fourier transform of the self-convolution of $f$ should be the same as the convolution of $c$.
    """)
    return


@app.cell
def _(c, ff_conv, np, plt):
    _imax = 10
    plt.plot(np.real(np.fft.fft(ff_conv))[:_imax])
    plt.plot(np.imag(np.fft.fft(ff_conv))[:_imax])
    plt.plot(np.real(np.fft.fft(c))[:_imax])
    plt.plot(np.imag(np.fft.fft(c))[:_imax])
    plt.show()
    plt.plot(np.real(np.fft.fft(ff_conv)) - np.real(np.fft.fft(c)))
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Alternatively, the FFT of convolution can be calculated by taking the FFT (DFT) of $f$ and multiplying this with itself. This should compare nicely to the FFT of the correlation function, $c$.
    """)
    return


@app.cell
def _(L_4, X_4, c, f_4, np, plt):
    _imax = 10
    ff_conv_fft = np.fft.fft(f_4) * np.fft.fft(f_4) * (L_4 / X_4.size) * (L_4 / X_4.size)
    c_conv_fft = np.fft.fft(c) * (L_4 / X_4.size)
    plt.plot(np.real(ff_conv_fft)[:_imax])
    plt.plot(np.real(c_conv_fft)[:_imax])
    plt.plot(np.abs(np.real(c_conv_fft)[:_imax]))
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The sign here is different, but the absolute values match. This is probably related to the fact that the function $f$ is just one of the possible solutions to $f* f = c$?

    Further, we may show the difference in using the explicit solution $f$, and the solution found by taking the positive square root of the correlation function in the FFT domain. This is not equivalent since the filters that are effectively used, are different
    """)
    return


@app.cell
def _(L_4, X_4, c, f_4, np, plt):
    np.random.seed(123)
    w_4 = np.fft.fft(np.random.normal(size=c.shape))
    plt.plot(np.fft.ifft(np.fft.fft(f_4) * L_4 / X_4.size * w_4))
    plt.plot(np.fft.ifft(np.sqrt(np.fft.fft(c) * L_4 / X_4.size) * w_4))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Both simulations behave similarly (similar curvature, max/min values, etc.), but they are not equal. We therefore investigate the filter that is being apploed in the second case.
    """)
    return


@app.cell
def _(L_4, X_4, c, np, plt):
    f2_fft = np.sqrt(np.fft.fft(c) * L_4 / X_4.size)
    f2_1 = np.real(np.fft.ifft(f2_fft) * X_4.size / L_4)
    plt.plot(f2_1)
    return (f2_1,)


@app.cell
def _(L_4, X_4, c, f2_1, np, plt):
    f2_double = np.hstack((f2_1, f2_1))
    f2_conv = np.convolve(f2_double, f2_1, 'valid') * L_4 / X_4.size
    plt.plot(f2_conv)
    plt.plot(c)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As we can see, this filter also satisfy $f * f = c$, which was intended by construction, but a double verification now proves its validity. Also, comparing the second filter with the explicit one shows two quite different filters.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Investigating the filter for longer ranges
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    v_6 = gaussianfft.variogram('gaussian', 1.0)
    L_5 = 0.5
    X_5 = np.linspace(0, L_5, 1025)
    _c_list = [v_6.corr(L_5 / 2 - x) for x in X_5]
    c_1 = np.array(_c_list)
    plt.plot(c_1)
    return L_5, X_5, c_1, v_6


@app.cell
def _(L_5, X_5, c_1, np, plt):
    f_5 = np.fft.ifft(np.sqrt(np.fft.fft(c_1) * L_5 / X_5.size)) * X_5.size / L_5
    plt.plot(np.real(f_5))
    plt.plot(np.imag(f_5))
    plt.show()
    f_double = np.real(np.hstack((f_5, f_5)))
    f_conv = np.convolve(f_double, np.real(f_5), 'valid') * L_5 / X_5.size
    plt.plot(f_conv)
    plt.plot(c_1)
    plt.show()
    return (f_5,)


@app.cell
def _(L_5, X_5, gaussianfft, plt, v_6):
    w_gaussianfft = gaussianfft.advanced.simulate(v_6, X_5.size, L_5 / X_5.size, padx=0)
    plt.plot(w_gaussianfft)
    return (w_gaussianfft,)


@app.cell
def _(f_5, np, plt, w_gaussianfft):
    w_5 = np.random.normal(size=(len(w_gaussianfft),))
    w_double = np.hstack((w_5, w_5))
    plt.plot(np.convolve(w_double, np.real(f_5), 'valid'))
    return (w_5,)


@app.cell
def _(f_5, np, plt, w_5):
    # Not to scale
    plt.plot(np.real(np.fft.ifft(np.fft.fft(w_5) * np.fft.fft(f_5))))
    return


@app.cell
def _(L_5, X_5, c_1, np, plt, w_5):
    # Not to scale
    dx = L_5 / X_5.size
    plt.plot(np.real(np.fft.ifft(np.fft.fft(w_5 / w_5.size) * np.sqrt(np.fft.fft(c_1)))))
    return


@app.cell
def _(w_gaussianfft):
    w_gaussianfft
    return


@app.cell
def _(f_5, np, plt):
    plt.plot(np.real(f_5))
    return


@app.cell
def _(f_5, np, plt):
    plt.plot(np.real(f_5[::-1]))
    return


@app.cell
def _(c_1, np):
    signs = (np.random.normal(size=c_1.shape) > 3.0) * 2 - 1
    signs = np.arange(0, c_1.size) % 2 * 2 - 1
    return (signs,)


@app.cell
def _(L_5, X_5, c_1, np, signs):
    f_mod = np.fft.ifft(signs * np.sqrt(np.fft.fft(c_1) * L_5 / X_5.size)) * X_5.size / L_5
    return (f_mod,)


@app.cell
def _(f_mod, np, plt):
    plt.plot(np.real(f_mod))
    return


@app.cell
def _(f_mod, np, plt, w_5):
    # Not to scale
    plt.plot(np.real(np.fft.ifft(np.fft.fft(w_5) * np.fft.fft(f_mod))))
    return


@app.cell
def _(c_1, np, plt):
    plt.plot(np.real(np.sqrt(np.fft.fft(c_1)))[:10], 'o-')
    return


@app.cell
def _(c_1, np, plt):
    plt.plot(np.imag(np.sqrt(np.fft.fft(c_1)))[:10])
    return


@app.cell
def _(f_5, np, plt):
    plt.plot(np.real(f_5))
    plt.plot(np.imag(f_5))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Finding the appropriate range thresholds

    This section assumes that for a given range, the filter becomes circular continuous. Until this range is reached, we have a degenerate case for the transformation of $w$ (at least for the default filter choice). The solution to this problem is probably to find a different filter function that satisfy $f* f = c$, but this is not covered in this section. One solution that may be investigated in the Gaussian case is to use an analytically calculated filter.
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    v_7 = gaussianfft.variogram('gaussian', 1.0)
    L_6 = 3
    X_6 = np.linspace(0, L_6, 1025)
    _c_list = [v_7.corr(L_6 / 2 - x) for x in X_6]
    c_2 = np.array(_c_list)
    plt.plot(c_2)
    return L_6, X_6, c_2


@app.cell
def _(L_6, X_6, c_2, np, plt):
    f_6 = np.fft.ifft(np.sqrt(np.fft.fft(c_2) * L_6 / X_6.size)) * X_6.size / L_6
    plt.plot(np.real(f_6))
    return


@app.cell
def _(gaussianfft, np):
    def analyze_filter_circ_diff(_vtype, r, Lmax):
        v = gaussianfft.variogram(_vtype, r)
        _lvals = np.arange(0.1, 1.0, 0.05) * Lmax
        _circ_diffs = []
        print('L        mean0   mean1   circdiff')
        for L in _lvals:
            X = np.linspace(0, L, 1025)
            _c_list = [v.corr(L / 2 - x) for x in X]
            c = np.array(_c_list)
            f = np.fft.ifft(np.sqrt(np.fft.fft(c) * L / X.size)) * X.size / L
            abs_diffs = np.abs(np.diff(np.real(f)))
            print('L={:.2f}   {:.4f}  {:.4f}  {:.4f}'.format(L, np.mean(abs_diffs[:100]), np.mean(abs_diffs[-100:]), np.abs(f[0] - f[-1])))
            _circ_diffs.append(np.abs(f[0] - f[-1]))
        return (_lvals, _circ_diffs)

    return (analyze_filter_circ_diff,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Gaussian
    """)
    return


@app.cell
def _(analyze_filter_circ_diff, plt):
    _lvals, _circ_diffs = analyze_filter_circ_diff('gaussian', 1.0, 10.0)
    plt.semilogy(_lvals, _circ_diffs, 'o')
    return


@app.cell
def _(analyze_filter_circ_diff, plt):
    _lvals, _circ_diffs = analyze_filter_circ_diff('gaussian', 2.0, 20.0)
    plt.semilogy(_lvals, _circ_diffs, 'o')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Spherical
    """)
    return


@app.cell
def _(analyze_filter_circ_diff, plt):
    _lvals, _circ_diffs = analyze_filter_circ_diff('spherical', 1.0, 2.5)
    plt.semilogy(_lvals, _circ_diffs, 'o')
    return


@app.cell
def _(gaussianfft, np, plt):
    v_8 = gaussianfft.variogram('matern52', 1.0)
    L_7 = 20
    X_7 = np.linspace(0, L_7, 1025)
    _c_list = [v_8.corr(L_7 / 2 - x) for x in X_7]
    c_3 = np.array(_c_list)
    plt.plot(c_3)
    return L_7, X_7, c_3


@app.cell
def _(L_7, X_7, c_3, corr_to_filter, plt):
    f_7 = corr_to_filter(c_3, L_7, X_7)
    plt.plot(f_7)
    return (f_7,)


@app.cell
def _(f_7, np, plt):
    np.random.seed(121314)
    w_6 = np.random.normal(size=f_7.shape)
    plt.plot(np.convolve(np.hstack((w_6, w_6)), f_7, 'valid'))
    return


@app.cell
def _(c_3, np):
    np.fft.fft(c_3)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Re-visiting the choice of filter

    The testing above have indicated that:
    - A circular continuous function $f$ is not a sufficient criteria for a proper filter
    - Not having a circular continuous function could also work (i.e. it may not even be necessary), although this is surprising. It could be that if the function is "close" to circular continuous, it is not visually possible to say that it is a valid function or not
    - There problem may be with the model and not the implementation

    To elaborate on the last point; the calculations should be correct. However, we have not inferred any restrictions on $c$ (other than that it should be a variogram-function). When applying the FFT (or perhaps just the convolution), we are implicitly adding features to $c$ which can make it non-positive definite. If $c$ is not positive definite, this is not a well-posed problem since the corresponding covariance matrix is not SPD.

    We therefore start by investigating how far from SPD the various functions are. According to Wikipedia, a function is positive definite if it is the Fourier transform of a function $g$ on the real line, with $g > 0$. (Correction: We are primarily interested in positive _semi_-definite function, which only slightly changes the above).

    First, an inspection of the resulting matrix and its positive semi-definiteness.
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    v_9 = gaussianfft.variogram('gaussian', 1.0)
    L_8 = 1
    X_8 = np.linspace(0, L_8 / 2, 63)
    _c_list = [v_9.corr(L_8 / 2 - x) for x in X_8]
    c_4 = np.array(_c_list)
    c_flat = np.array([v_9.corr(x) for x in X_8])
    plt.plot(c_flat)
    return (c_flat,)


@app.cell
def _(c_flat, np, plt):
    s_pre = np.outer(np.ones((c_flat.size,)), c_flat)

    for i in range(s_pre.shape[0]):
        s_pre[i] = np.roll(s_pre[i], i)
        s_pre[i, :i] = 0
    s = s_pre + s_pre.T - np.diag(np.diag(s_pre))

    plt.imshow(s)
    plt.colorbar()
    return (s,)


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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Experimenting with different ranges and lengths shows that in general, longer rangest yield a less positive semi-definite matrix (when the number of 0-valued eigenvalues are a metric for positive semi-definiteness). Short ranges converge $s$ towards the identity matrix.

    A conjecture that I have not found the proof of yet, although it may be trivial, is that the Fourier transform of a positive definite function is purely real and positive (?)
    """)
    return


@app.cell
def _(gaussianfft, np, plt):
    v_10 = gaussianfft.variogram('gaussian', 1.0)
    _lvals = np.arange(1.0, 5.0, 1)
    for L_9 in _lvals:
        X_9 = np.linspace(0, L_9, 1025)
        _c_list = [v_10.corr(L_9 / 2 - x) for x in X_9]
        c_5 = np.array(_c_list)
        plt.plot(np.abs(np.imag(np.fft.fft(c_5) * L_9 / X_9.size)[:10]))
    plt.legend(_lvals)
    return


@app.cell
def _(gaussianfft, np, plt):
    v_11 = gaussianfft.variogram('gaussian', 1.0)
    _lvals = np.arange(1.0, 5.0, 1)
    for L_10 in _lvals:
        X_10 = np.linspace(0, L_10, 1025)
        _c_list = [v_11.corr(L_10 / 2 - x) for x in X_10]
        c_6 = np.array(_c_list)
        plt.plot(np.real(np.fft.fft(c_6) * L_10 / X_10.size)[:5])
    plt.legend(_lvals)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This did not prove to be very useful.

    ### Re-visiting the analytical solution

    The current working hypothesis is that the correlation function becomes problematic when the range increases. One thing that has not been tested, though, is the analytical solution to the Gaussian variogram case for long ranges. If the working hypothesis is correct, then using the analytically found filter should also be problematic, even if regular convultion is performed.

    First, verify the procedure for a short range
    """)
    return


@app.cell
def _(corr_to_filter, gaussianfft, np, plt):
    v_12 = gaussianfft.variogram('gaussian', 1.0)
    L_11 = 8.0
    X_11 = np.linspace(0, L_11, 1025)
    _c_list = [v_12.corr(L_11 / 2 - x) for x in X_11]
    c_7 = np.array(_c_list)
    plt.plot(c_7)
    f_analytic = np.sqrt(np.sqrt(12 / np.pi)) * np.exp(-6 * np.square(L_11 / 2 - X_11))
    f_filtered = corr_to_filter(ccc=c_7, LLL=L_11, XXX=X_11)
    ff_conv_1 = L_11 / X_11.size * np.convolve(np.hstack((f_analytic, f_analytic)), f_analytic, 'valid')
    plt.plot(ff_conv_1)
    _ff_conv2 = L_11 / X_11.size * np.convolve(np.hstack((f_filtered, f_filtered)), f_filtered, 'valid')
    plt.plot(_ff_conv2)
    return f_analytic, f_filtered


@app.cell
def _(f_analytic, f_filtered, plt):
    plt.plot(f_analytic)
    plt.plot(f_filtered)
    return


@app.cell
def _(f_analytic, f_filtered, np, plt):
    np.random.seed(1325252)
    w_7 = np.random.normal(size=f_analytic.shape)
    _z_analytic = np.convolve(np.hstack((w_7, w_7)), f_analytic, 'valid')
    _z_filtered = np.convolve(np.hstack((w_7, w_7)), f_filtered, 'valid')
    plt.plot(_z_analytic)
    plt.plot(_z_filtered)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Looks fine. The analytic self-convolution is shifted, but that is no problem. Now copy-and-paste all the above and re-run with a longer, known to be problematic, range.
    """)
    return


@app.cell
def _(corr_to_filter, gaussianfft, np, plt):
    v_13 = gaussianfft.variogram('gaussian', 1.0)
    L_12 = 1.0
    X_12 = np.linspace(0, L_12, 1025)
    _c_list = [v_13.corr(L_12 / 2 - x) for x in X_12]
    c_8 = np.array(_c_list)
    plt.plot(c_8)
    f_analytic_1 = np.sqrt(np.sqrt(12 / np.pi)) * np.exp(-6 * np.square(L_12 / 2 - X_12))
    f_filtered_1 = corr_to_filter(ccc=c_8, LLL=L_12, XXX=X_12)
    ff_conv_2 = L_12 / X_12.size * np.convolve(np.hstack((f_analytic_1, f_analytic_1)), f_analytic_1, 'valid')
    plt.plot(ff_conv_2)
    _ff_conv2 = L_12 / X_12.size * np.convolve(np.hstack((f_filtered_1, f_filtered_1)), f_filtered_1, 'valid')
    plt.plot(_ff_conv2)
    return f_analytic_1, f_filtered_1


@app.cell
def _(f_analytic_1, f_filtered_1, plt):
    plt.plot(f_analytic_1)
    plt.plot(f_filtered_1)
    return


@app.cell
def _(f_analytic_1, f_filtered_1, np, plt):
    np.random.seed(1325252)
    w_8 = np.random.normal(size=f_analytic_1.shape)
    _z_analytic = np.convolve(np.hstack((w_8, w_8)), f_analytic_1, 'valid')
    _z_filtered = np.convolve(np.hstack((w_8, w_8)), f_filtered_1, 'valid')
    plt.plot(_z_analytic)
    plt.plot(_z_filtered)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The final result looks fine for the analytic solution, HOWEVER, the analytic self-convolution is not correct.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Summary

    The primary conclusion to this notebook is that long ranges compared to grid sizes are problematic, and the problem is that the correlation function is badly conditioned/not "sufficiently" positive semi-definite in these cases. The correlation function may have a positive semi-definite form, but in the context of taking its convolution, this form is no longer the one being applied.

    The path forward is to find a threshold for the range/grid-size relationship, that depends on the variogram type. This threshold will be utilized to determine the required grid size, and padding will be applied accordingly. This is to an extent exactly what is being done today, except that the current threshold is not variogram type dependent.

    The threshold approach introduces another issue; computation time. If the required padding makes the grid too large for practical purposes, we have a problem. We may argue, however, that if the padded grid is too large (in number of cells), then the resolution is too high compared to the expected variation of the data, and resampling the grid before simulation and  interpolating afterwards should not alter the results too significantly, assuming a proper interpolation scheme is used.
    """)
    return


if __name__ == "__main__":
    app.run()
