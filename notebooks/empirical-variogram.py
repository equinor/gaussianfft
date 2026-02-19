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
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.spatial.distance import cdist
    from gaussianfft.util import EmpiricalVariogram
    # '%matplotlib inline' command supported automatically in marimo
    plt.rcParams['figure.figsize'] = [10,7]
    return EmpiricalVariogram, gaussianfft, np, plt


@app.cell
def _(EmpiricalVariogram, gaussianfft):
    # Setup
    nx, ny, nz = 200, 200, 1
    dx, dy, dz = 20, 20, 20
    px, py, pz = 2*nx, 2*ny, 2*nz
    v = gaussianfft.variogram('gaussian', 500, 500, 500)
    ev = EmpiricalVariogram(v, nx, dx, ny, dy, nz, dz, px, py, pz)

    dr = 3 * dx
    true_variogram = ev.true_variogram(dr)[1]
    return dr, ev, true_variogram


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Estimation

    Estimating variance could make sense if we also included variance data from each simulation. As of now, it does not.
    """)
    return


@app.cell
def _():
    # Monkey patching for estimation validation (only valid when using origo as reference?)
    # ev.simulate = ev.dummy_sim
    return


@app.cell
def _(ev):
    # refs = ev.pick_reference_points('random', 10, seed=1323)
    refs = ev.pick_reference_points('regular', 30)
    return (refs,)


@app.cell
def _(dr, ev, np, refs):
    midpoints, rec_mean, n_samples, tdata, convrg = ev.estimate_variogram(500, dr, refs, analyze_convergence=1)
    print('Simulation time: {:.4} (sd: {:.4})'.format(np.mean(tdata['sim']), np.std(tdata['sim'])))
    print('Estimation time: {:.4} (sd: {:.4})'.format(np.mean(tdata['est']), np.std(tdata['est'])))
    return convrg, midpoints, n_samples, rec_mean


@app.cell
def _(midpoints, plt, rec_mean, true_variogram):
    plt.plot(midpoints, rec_mean)
    # plt.plot(midpoints, rec_mean + np.sqrt(rec_var), 'r--')
    # plt.plot(midpoints, rec_mean - np.sqrt(rec_var), 'r--')
    plt.plot(midpoints, true_variogram, 'g--')
    plt.show()
    return


@app.cell
def _(midpoints, n_samples, np, plt):
    plt.bar(midpoints, n_samples, width=np.diff(midpoints)[0])
    return


@app.cell
def _(convrg, np, plt):
    plt.plot(np.abs(np.argmax(convrg.deltas, axis=1)))
    plt.grid()
    return


@app.cell
def _(convrg, np, plt):
    plt.plot(np.abs(convrg.deltas)[:, 6])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Analysis

    EmpiricalVariogram works when there is sufficient padding. For the longest ranges, we may see some artifacts when the padding is large and the variogram range is short. This could simply be caused by a lack of samples, but that may not be the whole story. To verify this, we should try to run an estimation with a huge number of realizations. Another explanation could actually be numerical noise when calculating the mean. How we choose the reference points have not been tested rigorously, but it appears to be convenient to use a number of realizations.

    ## Ways forward for the EmpiricalVariogram class

    - Convergence analysis. We know the true variogram, so we can find, plot and analyze the convergence for each range bin as a function of the number of realizations. This can also be done outside the class, but this may not be as robust (we must at least implement a seeding mechanism). The main purpose of doing this is to identify when we have generated a sufficient number of realizations (for arbitrary input parameters).
    - Reference point dependent variogram estimation. It may be of interest to differentiate the variograms estimated in each reference point. For symmetric fields, there should ideally be no difference if the number of realizations is sufficiently high
    - Analyze ringing effects. Can we provoke generation of ringing effects, and will the empirical variogram pick up the effect?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Assessing ringing effects with the empirical variogram
    """)
    return


@app.cell
def _(EmpiricalVariogram, gaussianfft):
    # Setup
    nx_1, ny_1, nz_1 = (100, 1, 1)
    dx_1, dy_1, dz_1 = (10, 0, 0)
    pfac = 8.0
    px_1, py_1, pz_1 = (int(pfac * nx_1), int(pfac * ny_1), int(pfac * nz_1))
    v_1 = gaussianfft.variogram('gaussian', 1200)
    ev_1 = EmpiricalVariogram(v_1, nx_1, dx_1, ny_1, dy_1, nz_1, dz_1, px_1, py_1, pz_1)
    dr_1 = 1.0 * dx_1
    true_variogram_1 = ev_1.true_variogram(dr_1)[1]
    return dr_1, ev_1, true_variogram_1


@app.cell
def _(ev_1):
    # refs = ev.pick_reference_points('random', 10, seed=1323)
    refs_1 = ev_1.pick_reference_points('origo')
    return (refs_1,)


@app.cell
def _(dr_1, ev_1, refs_1):
    midpoints_1, rec_mean_1, n_samples_1, tdata_1, convrg_1 = ev_1.estimate_variogram(5000, dr_1, refs_1, analyze_convergence=10)
    return convrg_1, midpoints_1, rec_mean_1


@app.cell
def _(midpoints_1, plt, rec_mean_1, true_variogram_1):
    plt.plot(midpoints_1, rec_mean_1)
    plt.plot(midpoints_1, true_variogram_1, 'g--')
    plt.show()
    return


@app.cell
def _(convrg_1, np, plt):
    plt.plot(np.abs(convrg_1.deltas)[:, -5])
    return


@app.cell
def _(ev_1, plt):
    s = ev_1.simulate()
    s_flat = s.reshape((s.shape[0], -1))
    plt.imshow(s_flat, interpolation='None')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Convergence comparison
    """)
    return


@app.cell
def _(EmpiricalVariogram, gaussianfft):
    # Setup
    nx_2, ny_2, nz_2 = (40, 40, 1)
    dx_2, dy_2, dz_2 = (25, 25, 25)
    pfac_1 = 1
    px_2, py_2, pz_2 = (int(pfac_1 * nx_2), int(pfac_1 * ny_2), int(pfac_1 * nz_2))
    v_2 = gaussianfft.variogram('spherical', 1000, 1000, 1000)
    ev1 = EmpiricalVariogram(v_2, nx_2, dx_2, ny_2, dy_2, nz_2, dz_2, px_2, py_2, pz_2)
    dr_2 = 1.5 * dx_2
    true_variogram_2 = ev1.true_variogram(dr_2)[1]
    return dr_2, dx_2, dy_2, dz_2, ev1, nx_2, ny_2, nz_2, true_variogram_2, v_2


@app.cell
def _(EmpiricalVariogram, dx_2, dy_2, dz_2, nx_2, ny_2, nz_2, v_2):
    # Setup 2
    pfac_2 = 10
    px_3, py_3, pz_3 = (int(pfac_2 * nx_2), int(pfac_2 * ny_2), int(pfac_2 * nz_2))
    ev2 = EmpiricalVariogram(v_2, nx_2, dx_2, ny_2, dy_2, nz_2, dz_2, px_3, py_3, pz_3)
    return (ev2,)


@app.cell
def _(dr_2, ev1, ev2, ev_1):
    refs_2 = ev_1.pick_reference_points('center', 30)
    r1 = ev1.estimate_variogram(2000, dr_2, refs_2, analyze_convergence=5)
    r2 = ev2.estimate_variogram(2000, dr_2, refs_2, analyze_convergence=5)
    return r1, r2


@app.cell
def _(np, plt, r1, r2):
    col = 4
    plt.plot(np.abs(r1[4].deltas)[:, col])
    plt.plot(np.abs(r2[4].deltas)[:, col])
    return


@app.cell
def _(midpoints_1, plt, r1, r2, true_variogram_2):
    plt.plot(midpoints_1, r1[1])
    plt.plot(midpoints_1, r2[1])
    plt.plot(midpoints_1, true_variogram_2, 'r--')
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Padding/Range relationship
    """)
    return


@app.cell
def _(np):
    desired_range = np.linspace(8, 12, 6)
    desired_padding_f = np.arange(1, 11, 2) * 0.5
    return desired_padding_f, desired_range


@app.cell
def _(EmpiricalVariogram, desired_padding_f, desired_range, gaussianfft, np):
    gaussianfft.seed(12313)
    # Setup
    L = 1000
    n = 40
    d = L / n
    dr_3 = 1.5 * d
    vtype = 'gaussian'
    nmax = 600
    output_padding = []
    # Convert from aprx pl to exact
    for p in desired_padding_f:  # Actual padding (in number of gridcells)
        output_padding.append(int(p * L / d))
    output_padding_f = np.array(output_padding) / n
    v_3 = gaussianfft.variogram(vtype, desired_range[0] * L, desired_range[0] * L)
    ev_2 = EmpiricalVariogram(v_3, n, d, n, d, 1, 0, output_padding[0], output_padding[0], output_padding[0])
    # Prepare results
    refs_3 = ev_2.pick_reference_points('origo')
    mid, _, _, _, convrg_2 = ev_2.estimate_variogram(nmax, dr_3, refs_3, analyze_convergence=5)
    output_deltas = np.zeros((len(output_padding), len(desired_range), convrg_2.deltas.shape[1]))
    for i, r in enumerate(desired_range):
    # -----
        print('*** {}/{} ***'.format(i, len(desired_range)))
        for j, p in enumerate(output_padding):
            v_3 = gaussianfft.variogram(vtype, r * L, r * L)
            ev_2 = EmpiricalVariogram(v_3, n, d, n, d, 1, 0, p, p, p)
            refs_3 = ev_2.pick_reference_points('origo')
            mid, _, _, _, convrg_2 = ev_2.estimate_variogram(nmax, dr_3, refs_3, analyze_convergence=5)
            output_deltas[j, i, :] = convrg_2.deltas[-1]
    output_range = desired_range  # For notational purposes only
    return (
        L,
        d,
        dr_3,
        n,
        nmax,
        output_deltas,
        output_padding_f,
        output_range,
        refs_3,
        vtype,
    )


@app.cell
def _(np, output_deltas, output_padding_f, output_range, plt):
    plt.rcParams['figure.figsize'] = [20, 30]
    for ir in [1, 2, 3, 4]:
        plt.subplot(510 + ir)
        plt.title(output_range[ir])
        ndelta = output_deltas.shape[2]
        plt.contourf(np.arange(0, ndelta), output_padding_f, np.abs(output_deltas[:, ir, :]), 40, vmax=0.3)
        plt.colorbar()
    return


app._unparsable_cell(
    r"""
    res = np.zeros((len(ou), len(rl), 9))
    for j in range(output_deltas.shape[0]):
        for i in range(delta_res.shape[1]):
            res[j, i, 0] = np.max(np.abs(delta_res[j, i, :]))                    # Max error
            res[j, i, 1] = np.max(np.abs(delta_res[j, i, :int(0.25*len(mid))]))  # Max error, close
            res[j, i, 2] = np.max(np.abs(delta_res[j, i, :int(0.5*len(mid))]))   # Max error, half way
            res[j, i, 3] = np.mean(np.abs(delta_res[j, i, :]))                   # Mean error
            res[j, i, 4] = np.mean(np.abs(delta_res[j, i, :int(0.25*len(mid))])) # Mean error, close
            res[j, i, 5] = np.mean(np.abs(delta_res[j, i, :int(0.5*len(mid))])  # Mean error, half way
            res[j, i, 6] = np.sum(np.abs(delta_res[j, i, :]))                    # L1 error
            res[j, i, 7] = np.sum(np.abs(delta_res[j, i, :int(0.25*len(mid))]))  # L1 error, close
            res[j, i, 8] = np.sum(np.abs(delta_res[j, i, :int(0.5*len(mid))]))   # L1 error, half way
    """,
    name="_"
)


@app.cell
def _(res):
    selected_res = res[:, :, 2]
    return (selected_res,)


@app.cell
def _(pl_fraction, plt, rl, selected_res):
    plt.contourf(pl_fraction, rl, selected_res.T, 40)
    plt.colorbar()
    return


@app.cell
def _(
    EmpiricalVariogram,
    L,
    actual_pl,
    d,
    dr_3,
    gaussianfft,
    n,
    nmax,
    refs_3,
    rl,
    vtype,
):
    r_1 = rl[2]
    print(r_1)
    p_1 = actual_pl[-1]
    v_4 = gaussianfft.variogram(vtype, r_1 * L, r_1 * L)
    ev_3 = EmpiricalVariogram(v_4, n, d, n, d, 1, 0, p_1, p_1, p_1)
    mid_1, evario, _, _, convrg_3 = ev_3.estimate_variogram(nmax, dr_3, refs_3, analyze_convergence=5)
    return convrg_3, evario, mid_1


@app.cell
def _(convrg_3):
    convrg_3.deltas.shape
    return


@app.cell
def _(convrg_3, evario, mid_1, plt):
    plt.plot(mid_1, evario)
    plt.plot(mid_1, evario - convrg_3.deltas[-1, :])
    return


@app.cell
def _(convrg_3, plt):
    plt.plot(convrg_3.deltas[-1, :])
    return


@app.cell
def _(plt, selected_res):
    plt.imshow(selected_res, interpolation='None')
    plt.colorbar()
    return


@app.cell
def _(pl_fraction, rl, selected_res):
    from scipy.interpolate import interp2d
    finterp = interp2d(pl_fraction, rl, selected_res.T)
    return (finterp,)


@app.cell
def _(finterp, np, pl_fraction, rl):
    nix, niy = (30, 31)
    gridx = np.linspace(np.min(pl_fraction), np.max(pl_fraction), nix)
    gridy = np.linspace(np.min(rl), np.max(rl), niy)
    zinterp = np.zeros((nix, niy))
    for i_1, x in enumerate(gridx):
        for j_1, y in enumerate(gridy):
            zinterp[i_1, j_1] = finterp(x, y)
    return gridx, gridy, zinterp


@app.cell
def _(gridx, gridy, np, plt, zinterp):
    plt.contourf(gridx, gridy, np.log10(zinterp.T), 80)
    plt.grid()
    plt.colorbar()
    return


@app.cell
def _(np, plt, rl):
    plt.plot(np.exp(5)*rl, 'o')
    return


@app.cell
def _(np, selected_res):
    np.savetxt('res.csv', selected_res, delimiter=',', fmt='%.2f')
    return


if __name__ == "__main__":
    app.run()
