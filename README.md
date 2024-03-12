# Gaussianfft

A fast library for simulating Gaussian Random Fields in 1-, 2-, and 3-dimensional space, using the fast Fourier transform (Intel MKL).
It can handle very large grids (The ambition is to handle grid sizes of 1000 x 1000 x 1000 and greater).

Originally developed by [Norsk Regnesentral (NR)](https://nr.no) on commission from Equinor.
Documentation from Norsk Regnesentral: [SAND_04_18.pdf](https://github.com/equinor/gaussianfft/blob/master/doc/SAND_04_18.pdf)

## Usage

```bash
pip install gaussianfft
```

```python
import gaussianfft as grf

grf.seed(100)  # For deterministic / repeatable output
variogram = grf.variogram(grf.VariogramType.GAUSSIAN, 1000)

simulation = grf.simulate(variogram, nx=100, dx=1, ny=100, dy=1)  # 2D 100 x 100 grid
```

See [examples](examples/) for examples, getting started, and other documentation.


##  Description
Contact person in Norsk Regnesentral: [Petter Abrahamsen](mailto:Petter.Abrahamsen@nr.no) (2024)
Contact person in Equinor: [Oddvar Lia](mailto:olia@equinor.com)


Check Docstring for usage but a brief summary follows:

How to use it in python scripts called up from RMS:
1. Ensure it is installed, and available[^1]
2. In python script:
   ```python
   import gaussianfft as grf
   import numpy as np
   ```
3. Set variogram:
   `variogram = grf.variogram(variogram_name, main_range, perp_range, vert_range, azimuth, dip, power)`

   `variogram_name` is one of:
   * `exponential`
   * `spherical`
   * `gaussian`
   * `general_exponential`  (this is the only one using the exponent called power in the variogram function)
   * `matern32`
   * `matern52`
   * `matern72`
   * `constant`

   The ranges are given the same name as in IPL but corresponds to x,y,z directions.

   Note that the simulation is a regular 3D grid and the coordinate system is right-handed. This means that input azimuth angle should be  `(90 - azimut_used_in_rms)` for standard RMS grids which are left-handed.
   So if you want to use this in RMS and load the result into a zone in a grid in RMS (e.g by using Roxar API) then be aware of this.

4. Simulation is done by:

   `gauss_vector = grf.simulation(variogram, nx, dx, ny, dy, nz, dz)`

   The gauss field output is a 1D numpy array and by using

   `gauss_result = np.reshape(gauss_vector, (nx, ny, nz), order='F')`   one get a 3D numpy array

5. To check how large the extension of the internal simulation grid is (to avoid edge effects in the result from the FFT algorithm)
the grid is increased before it is simulated internally in the module. You can check this extension to see the actual grid size used.
This grid size is reported by using the function:

   ```python
   [nx_extended, ny_extended, nz_extended] = grf.simulation_size(variogram, nx, dx, ny, dy, nz, dz)
   ```

    and depends very much on the relative size of the correlation lengths and the grid size (length, width, height)

6. To get the start seed that is used:
  `seed = grf.seed()`

7. To set a seed before calling any simulation:
  `grf.seed(seed_value)`

**Note**: the returned seed from `grf.seed()` is created automatically by the clock time.
If you use multiprocessing, and run several processes in parallel be sure to delay start of a new process by at least 1 second after the previous process to avoid that two different processes get the same start seed.

The return seed is the same regardless of how many times you call simulation since it is the start seed of the first call to simulation.
It must however not be called before the first call to simulation if you want the start seed to be automatically generated.
If you want to run with a predefined start seed, call `grf.seed(seed_value)` before the first call to simulation.



## Building
We use [`scikit-build-core`](https://scikit-build-core.readthedocs.io/en/latest/index.html) as the build tool, in order to use [`pyproject.toml`](https://pip.pypa.io/en/stable/reference/build-system/pyproject-toml/) to facilitate easier building while using [`cmake`](https://cmake.org) to build the C++ extension.

We use [`pybind11`](https://pybind11.readthedocs.io/en/stable/) to create a Python module from the C++ source code.
When building with `-DCMAKE_BUILD_TARGET=Debug` (the default), [Boost::filesystem](https://www.boost.org/doc/libs/1_81_0/libs/filesystem/doc/index.htm).
By default, [Boost 1.81.0](https://www.boost.org/doc/libs/1_81_0/) will be used.
This can be overwritten by setting `-DBOOST_VERSION`.
You may want to create a virtual environment before building `gaussianfft`.

```bash
python -m venv venv
source venv/bin/activate
```

For the time being, Windows is not supported due to difficulties making `gaussianfft` compile there (on a windows runner on GitHub Actions).
Contributions for making it compile reliably on Windows are welcome.

The rest of this section assumes you are working on a UNIX-like system.
It has been tested on macOS (Intel/Apple Silicon) and Linux (x86).

If you are compiling `gaussianfft` for ARM / Aarch / Apple Silicon, ARM performance library must be installed.
Please follow [ARM's Install Guide](https://learn.arm.com/install-guides/armpl/) for instructions on how to install them.
The libraries are available for download [here](https://developer.arm.com/downloads/-/arm-performance-libraries).

To build the distribution wheel(s), run
```bash
export PYTHON=<which python to use>  # Only useful when not running in a virtual environment 
make build
```
This will build the binary, and source distributions with the [`build`](https://github.com/pypa/build) package in a temporary / ephemeral directory.
There is no caching of build artifacts in this case.

If you need to build, and iterate on the extension module, you may want to execute

```bash
cmake -S . -B build
cmake --build build
```

## Contributing
Report bugs (description with reproducible steps + run environment) and feature requests are welcome.

[^1]: If using [RMS](https://www.aspentech.com/en/products/sse/aspen-rms), make sure the path where `gaussianfft` is installed is available to RMS.
