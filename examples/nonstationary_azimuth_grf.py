import platform
import time
import matplotlib
if platform.system() == 'Linux':
    matplotlib.use('TkAgg')

import numpy as np
import matplotlib.pyplot as plt
import gaussianfft as grf


def rotating_azimuth(locations, centre=(495.0, 495.0)):
    """Azimuth (degrees, counter-clockwise from x) tangential to circles around ``centre``.

    Without shared noise, locations whose azimuths are more than one bin apart
    are uncorrelated. Near the centre the azimuth turns quickly.
    """
    angle = np.degrees(np.arctan2(locations[:, 1] - centre[1], locations[:, 0] - centre[0]))
    return (angle + 90.0) % 360.0


def main():
    # 100 x 100 x 5 grid
    nx, ny, nz = 100, 100, 5
    dx, dy, dz = 10.0, 10.0, 5.0
    shape = (nx, ny, nz)
    spacing = (dx, dy, dz)

    # Shared noise: all azimuth components are driven by the same white noise, so
    # correlation extends across azimuth bins, in both kriging and simulation.
    # A 3D grid is then simulated with a 3D FFT, also for a single layer, and the
    # FFT is padded in z by about the vertical correlation length (depth_range / dz).
    shared_noise = True
    variogram = grf.nonstationary_variogram(
        'matern52', main_range=300, perp_range=60, depth_range=20,
        azimuth_callable=rotating_azimuth, dip=10, n_bins=36, shared_noise=shared_noise,
    )
    x, y = np.meshgrid((np.arange(nx) + 0.5) * dx, (np.arange(ny) + 0.5) * dy, indexing='ij')
    azimuth = rotating_azimuth(np.column_stack((x.ravel(), y.ravel()))).reshape(nx, ny)

    # Unconditional simulation
    grf.seed(42)
    start = time.perf_counter()
    uncond = variogram.simulate(shape, spacing)
    print(f'Unconditional simulation: {time.perf_counter() - start:.2f} s')

    # Observation points at cell centers in layer 1
    rng = np.random.default_rng(1)
    obs_idx = rng.integers(5, 95, size=(8, 2))
    obs_pt = np.column_stack([(obs_idx + 0.5) * [dx, dy], np.full(len(obs_idx), dz / 2)])
    obs_val = np.ones(len(obs_idx))
    obs_unc = np.zeros(len(obs_idx))

    # Simple kriging prediction (mean 0) and a conditional simulation
    pred_mean, _ = grf.predict(variogram, shape, spacing, obs_pt, obs_val, obs_unc)
    grf.seed(42)
    sim, = grf.conditional_simulate(variogram, shape, spacing, obs_pt, obs_val, obs_unc)

    # Plot
    extent = [0, nx * dx, 0, ny * dy]
    vmin, vmax = -3, 3
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle(f'shared_noise={shared_noise}')

    ax = axes[0, 0]
    im = ax.imshow(azimuth.T, origin='lower', extent=extent, cmap='twilight', vmin=0, vmax=360)
    step = 8
    xs, ys = np.meshgrid((np.arange(0, nx, step) + 0.5) * dx, (np.arange(0, ny, step) + 0.5) * dy, indexing='ij')
    az = np.radians(azimuth[::step, ::step])
    ax.quiver(xs, ys, np.cos(az), np.sin(az),
              pivot='middle', headwidth=0, headlength=0, headaxislength=0)
    ax.set_title('Azimuth (deg, main range direction)')
    fig.colorbar(im, ax=ax)

    map_specs = [
        (axes[0, 1], uncond[:, :, 0],     'Unconditional sim (seed=42), layer 1', 'RdBu_r',  vmin, vmax, False),
        (axes[0, 2], pred_mean[:, :, 0],  'SK prediction (mean), layer 1',        'RdBu_r',  0, 1, True),
        (axes[1, 0], uncond[:, :, 4],     'Unconditional sim (seed=42), layer 5', 'RdBu_r',  vmin, vmax, False),
        (axes[1, 1], sim[:, :, 0],        'Cond. sim (seed=42), layer 1',         'RdBu_r',  vmin, vmax, True),
        (axes[1, 2], pred_mean[:, :, 4],  'SK prediction (mean), layer 5',        'RdBu_r',  0, 1, False),
    ]
    for ax, field, title, cmap, v0, v1, show_obs in map_specs:
        im = ax.imshow(field.T, origin='lower', extent=extent, vmin=v0, vmax=v1, cmap=cmap)
        if show_obs:
            ax.plot(obs_pt[:, 0], obs_pt[:, 1], 'ko', markersize=5)
        ax.set_title(title)
        fig.colorbar(im, ax=ax)

    for ax in axes.flat:
        ax.set_xlabel('x (m)')
        ax.set_ylabel('y (m)')
    fig.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
