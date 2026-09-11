import numpy as np
import xtgeo
from pathlib import Path

import gaussianfft as grf

OBS_UNCERTAINTY = 0.0  # uncertainty applied to blocked well data
# 0.01: Strict: honor observations almost exactly
# 1.0: Loose: observations are just hints

_HERE = Path(__file__).resolve().parent

# --- 1. Load grid and property ---
grid = xtgeo.grid_from_file(_HERE / "geogrid_volon.roff")
prop = xtgeo.gridproperty_from_file(_HERE / "geogrid_volon--trend_aps_channel.roff")
prop.name = "probcube_aps_Channel_fft_kriging"  # set name of updated property


# --- 2. Remember original mask for inactive cells ---
original_mask = np.ma.getmask(prop.values)

# --- 3. Load blocked well observations ---
blocked_wells = xtgeo.blockedwells_from_files(
    [
        _HERE / "geogrid_volon--55_33-1.bw",
        _HERE / "geogrid_volon--55_33-2.bw",
        _HERE / "geogrid_volon--55_33-3.bw",
        _HERE / "geogrid_volon--55_33-A-1.bw",
        _HERE / "geogrid_volon--55_33-A-2.bw",
        _HERE / "geogrid_volon--55_33-A-3.bw",
        _HERE / "geogrid_volon--55_33-A-4.bw",
        _HERE / "geogrid_volon--55_33-A-5.bw",
        _HERE / "geogrid_volon--55_33-A-6.bw",
    ]
)

obs_locations = []
obs_values_raw = []

for bw in blocked_wells:
    df = bw.dataframe
    sand = df["aps_Channel"].values
    mask = ~np.isnan(sand)
    obs_values_raw.append(sand[mask])

    # Get IJK indices directly from blocked well dataframe
    i_idx = df["I_INDEX"].values[mask]
    j_idx = df["J_INDEX"].values[mask]
    k_idx = df["K_INDEX"].values[mask]

    obs_locations.append(np.column_stack([i_idx, j_idx, k_idx]))


obs_locations = np.vstack(obs_locations)
obs_values_raw = np.concatenate(obs_values_raw)

# --- 4. Transform observations: subtract prior mean (matching RMS approach) ---
# RMS uses: Truncate (keep >= 0) + subtract mean of the data.
# We work directly in probability space with the prior field as mean.
obs_prob_clipped = np.clip(obs_values_raw, 0.0, 1.0)

# Prior mean field (probcube_aps_Channel) used as kriging mean
prior_prob_field = np.ma.filled(prop.values.copy(), fill_value=prop.values.mean())
prior_prob_field = np.clip(prior_prob_field, 0.0, 1.0)

# --- 5. Set up variogram and grid dimensions ---
nx, ny, nz = grid.ncol, grid.nrow, grid.nlay

dx = grid.get_dx().values.mean()
dy = grid.get_dy().values.mean()
dz = grid.get_dz().values.mean()

# Variogram ranges in cell units (scaled by cell size)
variogram = grf.variogram("spherical", 2000.0, 500.0, 5.0, azimuth=125.0)

# --- 6. Convert IJK indices to grid-local coordinates ---
# Grid nodes are at positions i*dx for i in 0..n-1
# IJK indices are 0-based, so index i maps directly to position i*dx
obs_locations_local = np.zeros_like(obs_locations, dtype=float)
obs_locations_local[:, 0] = obs_locations[:, 0] * dx
obs_locations_local[:, 1] = obs_locations[:, 1] * dy
obs_locations_local[:, 2] = obs_locations[:, 2] * dz

# Filter points outside bounds
grid_max = np.array([(nx - 1) * dx, (ny - 1) * dy, (nz - 1) * dz])
inside = np.all((obs_locations_local >= 0) & (obs_locations_local <= grid_max), axis=1)
obs_locations_local = obs_locations_local[inside]
obs_prob_clipped = obs_prob_clipped[inside]

print(f"Grid dimensions: nx={nx}, ny={ny}, nz={nz}")
print(f"Cell sizes: dx={dx:.2f}, dy={dy:.2f}, dz={dz:.2f}")
print(f"Grid extent: ({nx * dx:.0f}, {ny * dy:.0f}, {nz * dz:.0f})")
print(f"Obs range (local coords):")
print(f"  min: {obs_locations_local.min(axis=0)}")
print(f"  max: {obs_locations_local.max(axis=0)}")
print(f"Number of observations inside grid: {inside.sum()}")

# --- 7. Krig in probability space with prior field as mean ---
obs_uncertainties = np.full(len(obs_prob_clipped), OBS_UNCERTAINTY)

mean_field, std_field = grf.predict(
    variogram,
    nx,
    dx,
    obs_locations_local,
    obs_prob_clipped,
    obs_uncertainties,
    ny=ny,
    dy=dy,
    nz=nz,
    dz=dz,
    mean=prior_prob_field,
)

# --- 8. Clip to [0, 1] ---
updated_prob = np.clip(mean_field, 0.0, 1.0)

# --- 9. Re-apply mask: inactive cells stay inactive ---
if original_mask is not np.ma.nomask:
    updated_prob = np.ma.array(updated_prob, mask=original_mask)

# --- 10. Write back to xtgeo property ---
prop.values = updated_prob
prop.to_file(_HERE / "sand_prob_updated.roff")
print("Done! Saved sand_prob_updated.roff")
