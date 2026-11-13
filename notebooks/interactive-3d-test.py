import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full", html_head_file="camera-sync.html")


@app.function
def variogram_options():
    return {
        "Exponential": "exponential",
        "Gaussian": "gaussian",
        "Spherical": "spherical",
        "General exponential (power 1.5)": "general_exponential",
        "Matérn 3/2": "matern32",
        "Matérn 5/2": "matern52",
        "Matérn 7/2": "matern72",
    }


@app.function
def make_variogram_controls():
    import marimo as mo

    return (
        mo.ui.dropdown(variogram_options(), value="Exponential", label="Variogram", full_width=True),
        mo.ui.slider(
            0, 1200, step=5, value=750, label="Major horizontal range (m)", show_value=True, full_width=True
        ),
        mo.ui.slider(
            0, 1200, step=5, value=100, label="Minor horizontal range (m)", show_value=True, full_width=True
        ),
        mo.ui.slider(
            0, 1200, step=5, value=375, label="Vertical range (m)", show_value=True, full_width=True
        ),
        mo.ui.slider(0, 180, step=1, value=45, label="Azimuth (°)", show_value=True, full_width=True),
        mo.ui.slider(0, 90, step=5, value=45, label="Depth twist (nonstationarity) (°)", show_value=True, full_width=True),
        mo.ui.slider(
            0.02, 0.08, step=0.005, value=0.04, label="Porosity std. dev.", show_value=True, full_width=True
        ),
        mo.ui.slider(
            0.0, 0.02, step=0.001, value=0.005,
            label="Measurement error (std. dev.)", show_value=True, full_width=True,
        ),
    )


@app.function
def depth_twist_azimuth(locations, base_azimuth, twist_degrees):
    import numpy as np

    depth_fraction = np.clip(locations[:, 2] / 800.0, 0.0, 1.0)
    return (base_azimuth + twist_degrees * depth_fraction) % 180.0


@app.function
def bins_for_depth_twist(twist_degrees):
    import numpy as np

    return 12 + int(np.ceil(24.0 * np.clip(twist_degrees, 0.0, 90.0) / 90.0))


@app.function
def make_variogram(kind, major, minor, vertical, azimuth, twist):
    import gaussianfft as grf
    from gaussianfft._kriging.nonstationary_variogram import NonstationaryVariogram

    ranges = tuple(max(float(value), 1.0) for value in (major, minor, vertical))
    if twist > 0.0:
        return NonstationaryVariogram(
            kind,
            *ranges,
            azimuth=lambda locations: depth_twist_azimuth(
                locations, float(azimuth), float(twist)
            ),
            n_bins=bins_for_depth_twist(twist),
        )
    return grf.variogram(kind, *ranges, azimuth=azimuth)


@app.function
def simulate_field(model, shape, spacing):
    import numpy as np

    import gaussianfft as grf
    from gaussianfft._kriging.grid_spec import GridSpec
    from gaussianfft._kriging.nonstationary_variogram import NonstationaryVariogram

    if isinstance(model, NonstationaryVariogram):
        return model.simulate(GridSpec(shape, spacing))
    grid_args = tuple(value for size, step in zip(shape, spacing) for value in (size, step))
    return np.asarray(grf.simulate(model, *grid_args)).reshape(shape, order="F")


@app.function
def porosity_color_limits(*fields):
    import numpy as np

    lower = min(float(np.min(field)) for field in fields)
    upper = max(float(np.max(field)) for field in fields)
    if lower == upper:
        lower -= 1e-6
        upper += 1e-6
    return lower, upper


@app.function
def precompute_slices(values, axis, spacing, positions):
    import numpy as np

    slices = []
    for position in positions:
        grid_position = position / spacing[axis]
        lower_index = int(np.floor(grid_position))
        upper_index = min(lower_index + 1, values.shape[axis] - 1)
        fraction = grid_position - lower_index
        lower_values = np.take(values, lower_index, axis=axis)
        upper_values = np.take(values, upper_index, axis=axis)
        slices.append(lower_values * (1.0 - fraction) + upper_values * fraction)
    return slices


@app.cell
def setup_context():
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    from scipy.ndimage import map_coordinates

    import gaussianfft as grf

    mean_porosity = 0.22
    update_planes_during_drag = mo.ui.checkbox(
        value=False, label="Update planes during drag"
    )
    get_east_slice, set_east_slice = mo.state(150)
    get_north_slice, set_north_slice = mo.state(150)
    get_depth_slice, set_depth_slice = mo.state(800)
    return (
        get_depth_slice,
        get_east_slice,
        get_north_slice,
        go,
        grf,
        map_coordinates,
        mean_porosity,
        mo,
        np,
        set_depth_slice,
        set_east_slice,
        set_north_slice,
        update_planes_during_drag,
    )


@app.cell
def build_controls(
    get_depth_slice,
    get_east_slice,
    get_north_slice,
    mo,
    set_depth_slice,
    set_east_slice,
    set_north_slice,
    update_planes_during_drag,
):
    (
        variogram_type,
        horizontal_range,
        minor_horizontal_range,
        vertical_range,
        azimuth,
        azimuth_curvature,
        porosity_stddev,
        measurement_error,
    ) = make_variogram_controls()
    kriging_method = mo.ui.dropdown(
        {"Simple": "simple", "Ordinary": "ordinary"},
        value="Ordinary",
        label="Kriging",
    )
    resample = mo.ui.button(
        label="Resample field",
        value=0,
        on_click=lambda count: count + 1,
        tooltip="Generate a new reference field and well measurements",
    )
    grid_resolution = mo.ui.number(
        start=5.0,
        stop=100.0,
        step=1.0,
        value=25.0,
        label="Grid spacing (m)",
        full_width=True,
    )
    east_slice = mo.ui.slider(
        -25, 800, step=25, value=get_east_slice(), on_change=set_east_slice,
        label="East (m)", show_value=True,
        full_width=True,
        debounce=not update_planes_during_drag.value,
    )
    north_slice = mo.ui.slider(
        -25, 800, step=25, value=get_north_slice(), on_change=set_north_slice,
        label="North (m)", show_value=True,
        full_width=True,
        debounce=not update_planes_during_drag.value,
    )
    depth_slice = mo.ui.slider(
        -25, 800, step=25, value=get_depth_slice(), on_change=set_depth_slice,
        label="Depth (m)", show_value=True,
        full_width=True,
        debounce=not update_planes_during_drag.value,
    )
    return (
        azimuth,
        azimuth_curvature,
        depth_slice,
        east_slice,
        grid_resolution,
        horizontal_range,
        kriging_method,
        measurement_error,
        minor_horizontal_range,
        north_slice,
        porosity_stddev,
        resample,
        variogram_type,
        vertical_range,
    )


@app.cell
def build_estimation_controls(mo):
    same_as_ground_truth = mo.ui.checkbox(value=True, label="Same as ground truth")
    (
        estimation_variogram_type,
        estimation_horizontal_range,
        estimation_minor_horizontal_range,
        estimation_vertical_range,
        estimation_azimuth,
        estimation_azimuth_curvature,
        estimation_porosity_stddev,
        estimation_measurement_error,
    ) = make_variogram_controls()
    return (
        same_as_ground_truth,
        estimation_variogram_type,
        estimation_horizontal_range,
        estimation_minor_horizontal_range,
        estimation_vertical_range,
        estimation_azimuth,
        estimation_azimuth_curvature,
        estimation_porosity_stddev,
        estimation_measurement_error,
    )


@app.cell
def display_estimation_controls(
    mo,
    same_as_ground_truth,
    estimation_variogram_type,
    estimation_horizontal_range,
    estimation_minor_horizontal_range,
    estimation_vertical_range,
    estimation_azimuth,
    estimation_azimuth_curvature,
    estimation_porosity_stddev,
    estimation_measurement_error,
):
    estimation_controls = mo.vstack(
        [
            mo.md("**Estimation variogram**"),
            mo.vstack(
                [
                    estimation_variogram_type,
                    estimation_horizontal_range,
                    estimation_minor_horizontal_range,
                    estimation_vertical_range,
                    estimation_azimuth,
                    estimation_azimuth_curvature,
                    estimation_porosity_stddev,
                    estimation_measurement_error,
                ],
                align="start",
            ) if not same_as_ground_truth.value else mo.md(""),
        ],
        align="start",
    )
    return (estimation_controls,)


@app.cell
def display_controls(
    azimuth,
    azimuth_curvature,
    depth_slice,
    east_slice,
    estimation_controls,
    grid_resolution,
    horizontal_range,
    kriging_method,
    measurement_error,
    minor_horizontal_range,
    mo,
    north_slice,
    porosity_stddev,
    resample,
    resample_conditional,
    same_as_ground_truth,
    update_planes_during_drag,
    variogram_type,
    vertical_range,
):
    ground_truth_controls = mo.vstack(
        [
            mo.md("**Ground-truth variogram**"),
            variogram_type,
            horizontal_range,
            minor_horizontal_range,
            vertical_range,
            azimuth,
            azimuth_curvature,
            porosity_stddev,
            measurement_error,
        ],
        align="start",
    )
    model_controls = mo.Html(
        f"""
        <div style="display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:24px; width:100%;">
          <div>{ground_truth_controls.text}</div>
          <div>{estimation_controls.text}</div>
        </div>
        """
    )
    slice_controls = mo.Html(
        f"""
        <div style="display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:16px; width:100%;">
          <div>{east_slice.text}</div>
          <div>{north_slice.text}</div>
          <div>{depth_slice.text}</div>
        </div>
        """
    )
    controls = mo.vstack(
        [
            mo.hstack(
                [mo.md("**Slice positions**"), grid_resolution],
                justify="space-between",
                align="start",
            ),
            slice_controls,
            update_planes_during_drag,
            mo.hstack(
                [
                    kriging_method,
                    resample,
                    resample_conditional,
                ],
                justify="start",
                wrap=True,
            ),
            same_as_ground_truth,
            model_controls,
        ],
        align="start",
    )
    return (controls,)


@app.cell
def conditional_simulation_controls(mo):
    resample_conditional = mo.ui.button(
        label="Resample conditional simulation",
        value=0,
        on_click=lambda count: count + 1,
        tooltip="Draw another possible field using the same well measurements",
    )
    return (resample_conditional,)


@app.cell
def simulate_reference_field(
    azimuth,
    azimuth_curvature,
    grf,
    grid_resolution,
    horizontal_range,
    minor_horizontal_range,
    np,
    resample,
    variogram_type,
    vertical_range,
):
    grid_step = float(grid_resolution.value)
    grid_shape = (int(np.ceil(800 / grid_step)) + 1,) * 3
    grid_spacing = (grid_step,) * 3
    grid_axis = np.arange(grid_shape[0]) * grid_spacing[0]
    seed = 42 + resample.value
    grf.seed(seed)
    reference_variogram = make_variogram(
        variogram_type.value,
        horizontal_range.value,
        minor_horizontal_range.value,
        vertical_range.value,
        azimuth.value,
        azimuth_curvature.value,
    )
    reference_gaussian = simulate_field(reference_variogram, grid_shape, grid_spacing)
    return grid_axis, grid_shape, grid_spacing, reference_gaussian


@app.cell
def define_wells():
    well_specs = [
        ("Well A", 150.0, 150.0, 150.0, 650.0, "#ffffff"),
        ("Well B", 650.0, 650.0, 650.0, 150.0, "#ffffff"),
        ("Well C", 150.0, 650.0, 650.0, 650.0, "#ffffff"),
        ("Well D", 650.0, 150.0, 150.0, 150.0, "#ffffff"),
        ("Well E", 400.0, 400.0, 400.0, 400.0, "#ffffff"),
    ]
    return (well_specs,)


@app.cell
def sample_wells(
    grid_axis,
    grid_spacing,
    map_coordinates,
    mean_porosity,
    measurement_error,
    np,
    porosity_stddev,
    reference_gaussian,
    resample,
    well_specs,
):
    sample_targets = np.arange(0.0, 801.0, 50.0)
    sample_depth_indices = np.unique(
        np.clip(np.rint(sample_targets / grid_spacing[2]).astype(int), 0, len(grid_axis) - 1)
    )
    sample_depths = grid_axis[sample_depth_indices]
    observation_locations = []
    observation_latent_values = []
    observation_well_indices = []

    for observation_well_index, (
        _well_name,
        top_east,
        top_north,
        bottom_east,
        bottom_north,
        _color,
    ) in enumerate(well_specs):
        depth_fraction = sample_depths / 800.0
        well_east = top_east + (bottom_east - top_east) * depth_fraction
        well_north = top_north + (bottom_north - top_north) * depth_fraction
        well_locations = np.column_stack((well_east, well_north, sample_depths))
        observation_locations.extend(well_locations)
        grid_locations = well_locations / np.asarray(grid_spacing)
        observation_latent_values.extend(
            map_coordinates(reference_gaussian, grid_locations.T, order=1, mode="nearest")
        )
        observation_well_indices.extend([observation_well_index] * sample_depths.size)

    observation_locations = np.asarray(observation_locations)
    observation_latent_values = np.asarray(observation_latent_values)
    observation_well_indices = np.asarray(observation_well_indices)
    rng = np.random.default_rng(42 + resample.value)
    observed_porosity = (
        mean_porosity
        + porosity_stddev.value * observation_latent_values
        + rng.normal(0.0, measurement_error.value, observation_latent_values.size)
    )
    reference_porosity = mean_porosity + porosity_stddev.value * reference_gaussian
    return (
        observation_locations,
        observation_well_indices,
        observed_porosity,
        reference_porosity,
    )


@app.cell
def build_estimation_variogram(
    azimuth,
    azimuth_curvature,
    horizontal_range,
    minor_horizontal_range,
    variogram_type,
    vertical_range,
    same_as_ground_truth,
    estimation_variogram_type,
    estimation_horizontal_range,
    estimation_minor_horizontal_range,
    estimation_vertical_range,
    estimation_azimuth,
    estimation_azimuth_curvature,
    porosity_stddev,
    measurement_error,
    estimation_porosity_stddev,
    estimation_measurement_error,
):
    selected_controls = (
        (
            variogram_type, horizontal_range, minor_horizontal_range,
            vertical_range, azimuth, azimuth_curvature,
        )
        if same_as_ground_truth.value else
        (
            estimation_variogram_type, estimation_horizontal_range,
            estimation_minor_horizontal_range, estimation_vertical_range,
            estimation_azimuth, estimation_azimuth_curvature,
        )
    )
    model_variogram = make_variogram(*(control.value for control in selected_controls))
    model_porosity_stddev = (
        porosity_stddev.value if same_as_ground_truth.value else estimation_porosity_stddev.value
    )
    model_measurement_error = (
        measurement_error.value if same_as_ground_truth.value else estimation_measurement_error.value
    )
    return model_variogram, model_porosity_stddev, model_measurement_error


@app.cell
def normalize_estimation_observations(
    observed_porosity,
    mean_porosity,
    model_porosity_stddev,
    model_measurement_error,
    np,
):
    normalized_observations = (observed_porosity - mean_porosity) / model_porosity_stddev
    normalized_uncertainties = np.full(
        observed_porosity.shape, model_measurement_error / model_porosity_stddev
    )
    return normalized_observations, normalized_uncertainties


@app.cell
def krige_well_data(
    grf,
    grid_shape,
    grid_spacing,
    kriging_method,
    mean_porosity,
    model_variogram,
    normalized_observations,
    normalized_uncertainties,
    observation_locations,
    model_porosity_stddev,
):
    normalized_estimate, normalized_kriging_stddev = grf.predict(
        model_variogram,
        grid_shape,
        grid_spacing,
        observation_locations,
        normalized_observations,
        normalized_uncertainties,
        method=kriging_method.value,
        mean=0.0,
        calculate_stddev=True,
    )
    estimated_porosity = mean_porosity + model_porosity_stddev * normalized_estimate
    kriging_stddev = model_porosity_stddev * normalized_kriging_stddev
    return estimated_porosity, kriging_stddev


@app.cell
def simulate_conditional_field(
    grf,
    grid_shape,
    grid_spacing,
    kriging_method,
    mean_porosity,
    model_variogram,
    normalized_observations,
    normalized_uncertainties,
    observation_locations,
    model_porosity_stddev,
    resample_conditional,
):
    grf.seed(1_000_042 + resample_conditional.value)
    normalized_conditional = grf.conditional_simulate(
        model_variogram,
        grid_shape,
        grid_spacing,
        observation_locations,
        normalized_observations,
        normalized_uncertainties,
        method=kriging_method.value,
        mean=0.0,
        n=1,
    )[0]
    conditional_porosity = mean_porosity + model_porosity_stddev * normalized_conditional
    return (conditional_porosity,)


@app.cell
def prepare_slice_cache(
    estimated_porosity,
    grid_axis,
    grid_spacing,
    kriging_stddev,
    np,
    reference_porosity,
):
    slice_positions = tuple(range(0, 801, 25))
    east_grid, north_grid = np.meshgrid(grid_axis, grid_axis, indexing="ij")
    east_plane, depth_plane = np.meshgrid(grid_axis, grid_axis, indexing="ij")
    north_plane, depth_plane_for_east = np.meshgrid(
        grid_axis, grid_axis, indexing="ij"
    )

    slice_cache = {
        "truth": {
            "east": precompute_slices(reference_porosity, axis=0, spacing=grid_spacing, positions=slice_positions),
            "north": precompute_slices(reference_porosity, axis=1, spacing=grid_spacing, positions=slice_positions),
            "depth": precompute_slices(reference_porosity, axis=2, spacing=grid_spacing, positions=slice_positions),
        },
        "estimate": {
            "east": precompute_slices(estimated_porosity, axis=0, spacing=grid_spacing, positions=slice_positions),
            "north": precompute_slices(estimated_porosity, axis=1, spacing=grid_spacing, positions=slice_positions),
            "depth": precompute_slices(estimated_porosity, axis=2, spacing=grid_spacing, positions=slice_positions),
        },
        "uncertainty": {
            "east": precompute_slices(kriging_stddev, axis=0, spacing=grid_spacing, positions=slice_positions),
            "north": precompute_slices(kriging_stddev, axis=1, spacing=grid_spacing, positions=slice_positions),
            "depth": precompute_slices(kriging_stddev, axis=2, spacing=grid_spacing, positions=slice_positions),
        },
    }
    return (
        depth_plane,
        depth_plane_for_east,
        east_grid,
        east_plane,
        north_grid,
        north_plane,
        slice_cache,
        slice_positions,
    )


@app.cell
def prepare_conditional_slice_cache(
    conditional_porosity,
    grid_spacing,
    slice_positions,
):
    conditional_slice_cache = {
        direction: precompute_slices(
            conditional_porosity, axis=axis, spacing=grid_spacing, positions=slice_positions
        )
        for axis, direction in enumerate(("east", "north", "depth"))
    }
    return (conditional_slice_cache,)


@app.cell
def render_comparison_views(
    conditional_porosity,
    conditional_slice_cache,
    depth_plane,
    depth_plane_for_east,
    depth_slice,
    east_grid,
    east_plane,
    east_slice,
    estimated_porosity,
    go,
    kriging_stddev,
    mo,
    north_grid,
    north_plane,
    north_slice,
    np,
    observation_locations,
    observation_well_indices,
    observed_porosity,
    reference_porosity,
    slice_cache,
    slice_positions,
    well_specs,
):
    porosity_lower, porosity_upper = porosity_color_limits(
        reference_porosity, estimated_porosity, conditional_porosity
    )
    uncertainty_upper = max(float(np.max(kriging_stddev)), 1e-6)

    def make_view(slice_group, title, lower, upper, colorscale, colorbar_title):
        fig = go.Figure()
        slice_surfaces = []
        if depth_slice.value >= 0:
            slice_surfaces.append(
                (
                    east_grid,
                    north_grid,
                    np.full_like(east_grid, depth_slice.value),
                    slice_group["depth"][slice_positions.index(depth_slice.value)],
                    "Depth slice",
                )
            )
        if north_slice.value >= 0:
            slice_surfaces.append(
                (
                    east_plane,
                    np.full_like(east_plane, north_slice.value),
                    depth_plane,
                    slice_group["north"][slice_positions.index(north_slice.value)],
                    "North slice",
                )
            )
        if east_slice.value >= 0:
            slice_surfaces.append(
                (
                    np.full_like(north_plane, east_slice.value),
                    north_plane,
                    depth_plane_for_east,
                    slice_group["east"][slice_positions.index(east_slice.value)],
                    "East slice",
                )
            )

        for slice_number, (slice_east, slice_north, slice_depth, slice_values, name) in enumerate(slice_surfaces):
            fig.add_trace(
                go.Surface(
                    x=slice_east,
                    y=slice_north,
                    z=slice_depth,
                    surfacecolor=slice_values,
                    cmin=lower,
                    cmax=upper,
                    colorscale=colorscale,
                    opacity=0.82,
                    showscale=slice_number == 0,
                    colorbar={"title": colorbar_title},
                    name=name,
                    hovertemplate=(
                        "East: %{x:.0f} m<br>North: %{y:.0f} m<br>"
                        "Depth: %{z:.0f} m<extra></extra>"
                    ),
                )
            )

        for plot_well_index, (
            well_name,
            top_east,
            top_north,
            bottom_east,
            bottom_north,
            well_color,
        ) in enumerate(well_specs):
            fig.add_trace(
                go.Scatter3d(
                    x=[top_east, bottom_east],
                    y=[top_north, bottom_north],
                    z=[0, 800],
                    mode="lines",
                    line={"color": well_color, "width": 7},
                    name=well_name,
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
            selected = observation_well_indices == plot_well_index
            well_samples = observation_locations[selected]
            fig.add_trace(
                go.Scatter3d(
                    x=well_samples[:, 0],
                    y=well_samples[:, 1],
                    z=well_samples[:, 2],
                    mode="markers",
                    marker={"color": well_color, "size": 5},
                    customdata=observed_porosity[selected],
                    name=f"{well_name} measurements",
                    hovertemplate=(
                        f"{well_name}<br>Depth: %{{z:.0f}} m<br>"
                        "Measured porosity: %{customdata:.3f}<extra></extra>"
                    ),
                    showlegend=False,
                )
            )

        fig.update_layout(
            title=title,
            width=460,
            height=460,
            uirevision="synchronized-camera",
            scene={
                "xaxis_title": "",
                "yaxis_title": "",
                "zaxis_title": "",
                "zaxis": {"autorange": "reversed"},
                "aspectmode": "cube",
                "uirevision": "synchronized-camera",
            },
            margin={"l": 0, "r": 0, "t": 45, "b": 0},
            legend={"yanchor": "top", "y": 0.98, "xanchor": "left", "x": 0.02},
        )
        return mo.ui.plotly(fig, config={"responsive": False})

    views = mo.Html(
        """
        <div style="display:grid; grid-template-columns:repeat(2, 460px); gap:8px; width:928px;">
          <div>{truth}</div>
          <div>{estimate}</div>
          <div>{conditional}</div>
          <div>{uncertainty}</div>
        </div>
        """
    ).batch(
        truth=make_view(
            slice_cache["truth"],
            "Ground truth",
            porosity_lower,
            porosity_upper,
            "Viridis",
            "Porosity",
        ),
        estimate=make_view(
            slice_cache["estimate"],
            "Kriged estimate",
            porosity_lower,
            porosity_upper,
            "Viridis",
            "Porosity",
        ),
        uncertainty=make_view(
            slice_cache["uncertainty"],
            "Kriging uncertainty",
            0.0,
            uncertainty_upper,
            "Magma_r",
            "Std. dev.",
        ),
        conditional=make_view(
            conditional_slice_cache,
            "Conditional simulation",
            porosity_lower,
            porosity_upper,
            "Viridis",
            "Porosity",
        ),
    )
    return (views,)


@app.cell
def select_profile_well(mo, well_specs):
    profile_well = mo.ui.dropdown(
        {well[0]: index for index, well in enumerate(well_specs)},
        value=well_specs[0][0],
        label="Well profile",
        full_width=True,
    )
    return (profile_well,)


@app.cell
def render_well_profile(
    conditional_porosity,
    estimated_porosity,
    go,
    grid_spacing,
    map_coordinates,
    measurement_error,
    mo,
    np,
    observation_locations,
    observation_well_indices,
    observed_porosity,
    profile_well,
    reference_porosity,
    well_specs,
):
    from plotly.colors import sample_colorscale

    selected_well = profile_well.value
    _profile_name, _top_east, _top_north, _bottom_east, _bottom_north, _color = well_specs[selected_well]
    top = np.array([_top_east, _top_north, 0.0])
    direction = np.array([_bottom_east - _top_east, _bottom_north - _top_north, 800.0])
    selected_observations = observation_well_indices == selected_well
    well_observations = observation_locations[selected_observations]
    observation_fractions = well_observations[:, 2] / 800.0
    fractions = np.unique(np.concatenate((
        np.linspace(0.0, max(1.0, float(np.max(observation_fractions))), 201),
        observation_fractions,
    )))
    profile_locations = top + fractions[:, None] * direction
    profile_coords = (profile_locations / np.asarray(grid_spacing)).T
    well_distance = fractions * np.linalg.norm(direction)
    observation_distance = observation_fractions * np.linalg.norm(direction)
    profile_estimate = map_coordinates(estimated_porosity, profile_coords, order=1, mode="nearest")
    profile_truth = map_coordinates(reference_porosity, profile_coords, order=1, mode="nearest")
    profile_lower, profile_upper = porosity_color_limits(
        reference_porosity, estimated_porosity, conditional_porosity
    )

    profile_figure = go.Figure()
    profile_figure.add_trace(go.Scatter(
        x=profile_estimate,
        y=well_distance,
        mode="lines",
        line={"color": "#000000", "dash": "dash", "width": 2},
        name="Est.",
        hovertemplate="Estimated: %{x:.3f}<br>Along well: %{y:.1f} m<extra></extra>",
    ))
    # Plotly line colors are scalar; group short segments into 32 shared-scale colors.
    segment_values = 0.5 * (profile_truth[:-1] + profile_truth[1:])
    color_bins = np.clip(
        ((segment_values - profile_lower) / (profile_upper - profile_lower) * 32).astype(int),
        0, 31,
    )
    for color_number, color_bin in enumerate(np.unique(color_bins)):
        segment_indices = np.flatnonzero(color_bins == color_bin)
        segment_x = []
        segment_y = []
        for segment_index in segment_indices:
            segment_x.extend([profile_truth[segment_index], profile_truth[segment_index + 1], None])
            segment_y.extend([well_distance[segment_index], well_distance[segment_index + 1], None])
        profile_figure.add_trace(go.Scatter(
            x=segment_x,
            y=segment_y,
            mode="lines",
            line={"color": sample_colorscale("Viridis", [(color_bin + 0.5) / 32])[0], "dash": "solid", "width": 3},
            name="True",
            legendgroup="truth",
            showlegend=color_number == 0,
            hovertemplate="True: %{x:.3f}<br>Along well: %{y:.1f} m<extra></extra>",
        ))
    profile_figure.add_trace(go.Scatter(
        x=observed_porosity[selected_observations],
        y=observation_distance,
        mode="markers",
        marker={
            "color": observed_porosity[selected_observations],
            "colorscale": "Viridis",
            "cmin": profile_lower,
            "cmax": profile_upper,
            "size": 7,
            "line": {"color": "#333333", "width": 1},
        },
        error_x={
            "type": "constant", "value": measurement_error.value,
            "color": "#666666", "thickness": 1, "width": 3,
        },
        name="Observed (±1σ noise)",
        showlegend=False,
        hovertemplate="Observed: %{x:.3f}<br>Along well: %{y:.1f} m<extra></extra>",
    ))
    profile_figure.update_layout(
        width=340,
        height=865,
        xaxis={"title": "Porosity", "zeroline": False},
        yaxis={"title": "Distance along well (m)", "autorange": "reversed"},
        legend={"x": 0.99, "y": 0.01, "xanchor": "right", "yanchor": "bottom", "bgcolor": "rgba(255,255,255,0.8)"},
        margin={"l": 65, "r": 15, "t": 10, "b": 50},
    )
    well_profile = mo.ui.plotly(profile_figure, config={"responsive": False})
    return well_profile, profile_figure


@app.cell
def display_dashboard(controls, mo, profile_well, views, well_profile):
    profile_panel = mo.vstack([profile_well, well_profile], align="start")
    dashboard = mo.Html(
        f"""
        <div style="display:flex; align-items:flex-start; gap:24px; width:100%; overflow-x:auto;">
          <aside style="flex:0 0 680px; width:680px; padding:16px; box-sizing:border-box; border:1px solid #ddd; border-radius:8px;">{controls.text}</aside>
          <div style="flex:0 0 928px;">{views.text}</div>
          <div style="flex:0 0 340px; width:340px;">{profile_panel.text}</div>
        </div>
        """
    )
    dashboard


if __name__ == "__main__":
    app.run()
