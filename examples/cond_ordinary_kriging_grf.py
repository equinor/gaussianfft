import platform
import matplotlib
if platform.system() == 'Linux':
    matplotlib.use('TkAgg')

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import map_coordinates
import gaussianfft as grf
from gaussianfft._kriging.kriging_toolkit import OrdinaryKriging


def _interp(field, xs, ys, dx, dy):
    return map_coordinates(field, [xs / dx, ys / dy], order=1, mode='nearest')


def main():
    # Grid setup
    nx, ny = 100, 100
    dx, dy = 10.0, 10.0
    variogram = grf.variogram('matern52', main_range=300, perp_range=100, azimuth=30)

    # Observation points
    obs_pt = np.array([[250.0, 750.0], [755.0, 255.0], [500.0, 500.0]])
    obs_val = np.array([2.5, -2.0, 0.5])
    obs_unc = np.array([0.0, 0.0, 0.0])

    # Ordinary kriging prediction
    ok = OrdinaryKriging(variogram, nx, dx, ny, dy, 1, 1.0, obs_pt, obs_val, obs_unc)
    pred_mean, pred_std = ok.predict()
    estimated_mean = ok.estimated_mean

    # Two conditional simulations
    sim_a = grf.conditional_simulate(
        variogram, nx, dx, ny, dy, obs_pt, obs_val, obs_unc,
        n=1, seed=42, method='OrdinaryKriging',
    )[0]
    sim_b = grf.conditional_simulate(
        variogram, nx, dx, ny, dy, obs_pt, obs_val, obs_unc,
        n=1, seed=123, method='OrdinaryKriging',
    )[0]

    # Cross-section: diagonal line through first two observations
    p0 = obs_pt[0]
    p1 = obs_pt[1]
    direction = p1 - p0
    length = np.linalg.norm(direction)
    unit = direction / length
    # Extend 150 m beyond each end
    start = p0 - 150.0 * unit
    end = p1 + 150.0 * unit
    s = np.linspace(0.0, 1.0, 500)
    line_x = start[0] + s * (end[0] - start[0])
    line_y = start[1] + s * (end[1] - start[1])
    dist = s * np.linalg.norm(end - start)
    # Projected arc-length positions of each observation along the section
    obs_proj = [np.dot(obs_pt[i] - start, unit) for i in range(len(obs_pt))]

    # Plot: 2x2 maps + cross-section spanning full width
    extent = [0, nx * dx, 0, ny * dy]
    vmin, vmax = -3, 3

    fig = plt.figure(figsize=(12, 11))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.7], hspace=0.4, wspace=0.35)

    map_specs = [
        (gs[0, 0], pred_mean,  'OK prediction (mean)',     'RdBu_r',  vmin,         vmax),
        (gs[0, 1], pred_std,   'OK prediction (std dev)',  'viridis',  0,            pred_std.max()),
        (gs[1, 0], sim_a,      'Cond. sim (seed=42)',      'RdBu_r',  vmin,         vmax),
        (gs[1, 1], sim_b,      'Cond. sim (seed=123)',     'RdBu_r',  vmin,         vmax),
    ]

    for spec, field, title, cmap, v0, v1 in map_specs:
        ax = fig.add_subplot(spec)
        im = ax.imshow(field.T, origin='lower', extent=extent,
                       vmin=v0, vmax=v1, cmap=cmap)
        # Cross-section line
        ax.plot([start[0], end[0]], [start[1], end[1]], 'k--', lw=1, alpha=0.6)
        ax.plot(obs_pt[:, 0], obs_pt[:, 1], 'ko', markersize=6)
        for i, v in enumerate(obs_val):
            ax.annotate(f'{v:.1f}', obs_pt[i], textcoords='offset points',
                        xytext=(4, 4), color='k', fontsize=8)
        ax.set_title(title)
        ax.set_xlabel('x (m)')
        ax.set_ylabel('y (m)')
        fig.colorbar(im, ax=ax)

    # Cross-section panel
    ax_cs = fig.add_subplot(gs[2, :])
    cs_mean = _interp(pred_mean, line_x, line_y, dx, dy)
    cs_std  = _interp(pred_std,  line_x, line_y, dx, dy)
    cs_a    = _interp(sim_a,     line_x, line_y, dx, dy)
    cs_b    = _interp(sim_b,     line_x, line_y, dx, dy)

    ax_cs.fill_between(dist, cs_mean - cs_std, cs_mean + cs_std,
                        alpha=0.25, color='C0', label='Mean ± std dev')
    ax_cs.plot(dist, cs_mean, color='C0', lw=1.8, label='OK mean')
    ax_cs.axhline(estimated_mean, color='k', lw=1.2, ls='--',
                  label=f'Estimated mean ({estimated_mean:.2f})')
    ax_cs.plot(dist, cs_a,    color='C1', lw=1.2, label='Cond. sim (seed=42)')
    ax_cs.plot(dist, cs_b,    color='C2', lw=1.2, label='Cond. sim (seed=123)')

    for i, sx in enumerate(obs_proj):
        if 0 <= sx <= dist[-1]:
            ax_cs.axvline(sx, color='k', lw=0.8, ls=':', alpha=0.5)
            ax_cs.plot(sx, obs_val[i], 'ko', markersize=7, zorder=5,
                       label='Observation' if i == 0 else '')

    ax_cs.set_xlabel('Distance along section (m)')
    ax_cs.set_ylabel('Value')
    ax_cs.legend(loc='best', ncol=2, fontsize=8)
    ax_cs.grid(True, alpha=0.3)
    ax_cs.set_title('Cross-section')

    plt.show()


if __name__ == '__main__':
    main()
