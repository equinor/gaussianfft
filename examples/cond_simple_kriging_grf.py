import platform
import matplotlib
if platform.system() == 'Linux':
    matplotlib.use('TkAgg')

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import map_coordinates
import gaussianfft as grf


def bilinear_interpolate(field, xs, ys, dx, dy):
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

    # Unconditional + conditional realizations for the same setup.
    grf.seed(42)
    uncond = grf.simulate(variogram, nx, dx, ny, dy)
    uncond_2d = np.array(uncond).reshape((nx, ny), order='F')
    cond_seed_42 = grf.conditional_simulate(
        variogram, nx, dx, ny, dy, obs_pt, obs_val, obs_unc, n=1, seed=42
    )[0]
    cond_seed_123 = grf.conditional_simulate(
        variogram, nx, dx, ny, dy, obs_pt, obs_val, obs_unc, n=1, seed=123
    )[0]

    # Preserve the "average of many conditional realizations" point.
    n_realizations = 100
    cond_stack = grf.conditional_simulate(
        variogram, nx, dx, ny, dy, obs_pt, obs_val, obs_unc, n=n_realizations
    )
    avg_cond = np.mean(cond_stack, axis=0)

    # Two prediction setups: mean=unconditional and mean=0.
    pred_with_uncond, _std_with_uncond = grf.predict(
        variogram, nx, dx, ny, dy, obs_pt, obs_val, obs_unc, mean=uncond_2d
    )
    pred_zero_mean, std_zero_mean = grf.predict(
        variogram, nx, dx, ny, dy, obs_pt, obs_val, obs_unc, mean=0.0
    )

    # Cross-section through observations
    p0_obs = obs_pt[0]
    p1_obs = obs_pt[1]
    obs_direction = p1_obs - p0_obs
    obs_dist = np.linalg.norm(obs_direction)
    obs_direction_unit = obs_direction / obs_dist
    p0 = p0_obs - 200.0 * obs_direction_unit
    p1 = p1_obs + 200.0 * obs_direction_unit
    s = np.linspace(0.0, 1.0, 400)
    line_x = p0[0] + s * (p1[0] - p0[0])
    line_y = p0[1] + s * (p1[1] - p0[1])
    arclen = np.hypot(p1[0] - p0[0], p1[1] - p0[1])
    dist = s * arclen
    obs_proj_dist = np.array([np.dot(obs_pt[i] - p0, obs_direction_unit) for i in range(len(obs_pt))])

    # Plot: 2x3 maps + cross-section panel.
    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 0.9])
    map_axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[0, 2]),
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1]),
        fig.add_subplot(gs[1, 2]),
    ]
    ax_cs = fig.add_subplot(gs[2, :])

    vmin, vmax = -3, 3
    extent = [0, nx * dx, 0, ny * dy]
    map_fields = [
        (uncond_2d, 'Unconditional (42)'),
        (cond_seed_42, 'Conditional SK (42)'),
        (avg_cond, f'Mean of {n_realizations} cond SK sims'),
        (cond_seed_123, 'Conditional SK (123)'),
        (pred_with_uncond, 'Prediction (mean=uncond)'),
        (pred_zero_mean, 'Prediction (mean=0)'),
    ]

    for ax, (field, title) in zip(map_axes, map_fields):
        im = ax.imshow(field.T, origin='lower', extent=extent, vmin=vmin, vmax=vmax, cmap='RdBu_r')
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], 'k--', lw=1)
        ax.plot(obs_pt[:, 0], obs_pt[:, 1], 'ko', markersize=6)
        for i, v in enumerate(obs_val):
            ax.annotate(f'{v:.1f}', obs_pt[i], textcoords='offset points', xytext=(4, 4))
        ax.set_title(title)
        ax.set_xlabel('x (m)')
        ax.set_ylabel('y (m)')
        fig.colorbar(im, ax=ax)

    # Cross-section panel (band shown for mean=0).
    pred_zero_cs = bilinear_interpolate(pred_zero_mean, line_x, line_y, dx, dy)
    std_zero_cs = bilinear_interpolate(std_zero_mean, line_x, line_y, dx, dy)

    ax_cs.fill_between(
        dist, pred_zero_cs - std_zero_cs, pred_zero_cs + std_zero_cs,
        alpha=0.2, color='C2', label='+-1 std dev (mean=0)'
    )
    ax_cs.plot(dist, bilinear_interpolate(uncond_2d, line_x, line_y, dx, dy), label='Unconditional (seed=42)', lw=1.2)
    ax_cs.plot(dist, bilinear_interpolate(cond_seed_42, line_x, line_y, dx, dy), label='Conditional SK (seed=42)', lw=1.3)
    ax_cs.plot(dist, bilinear_interpolate(cond_seed_123, line_x, line_y, dx, dy), label='Conditional SK (seed=123)', lw=1.3)
    ax_cs.plot(dist, pred_zero_cs, label='SK predict (mean=0)', lw=1.5, ls='--', color='C2')

    for i, sx in enumerate(obs_proj_dist):
        ax_cs.axvline(sx, color='k', lw=0.5, alpha=0.3)
        obs_std = obs_unc[i]
        ax_cs.plot(sx, obs_val[i], 'ko', markersize=7, zorder=5, label='Observation' if i == 0 else '')
        if obs_std > 0:
            ax_cs.errorbar(
                sx, obs_val[i], yerr=obs_std, fmt='none', ecolor='r',
                capsize=4, capthick=1.5, zorder=5
            )

    ax_cs.set_xlabel('Distance along section (m)')
    ax_cs.set_ylabel('Value')
    ax_cs.legend(loc='best', ncol=2)
    ax_cs.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
