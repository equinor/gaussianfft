# Gaussianfft

A fast library for simulating Gaussian Random Fields, using the fast Fourier transform (Intel MKL).

Originally developed by Norsk Regnesentral on commission from Equinor.
Documentation from Norsk Regnesentral: [SAND_04_18.pdf](doc/SAND_04_18.pdf) ([also available on GitHub](https://github.com/equinor/gaussianfft/blob/master/doc/SAND_04_18.pdf))

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


## Previous versions

### nrlib version pr 28.02.2018  for RMS10 is the final version compiled for RMS10
The directory  for this version: nrlib-dist-RMS10-180228
Compatibility: Compatible with python 3.4 which is used in RMS10

### nrlib version pr 28.02.2018  for RMS11Beta is the final version compiled for RMS11Beta
The directory  for this version: nrlib-dist-RMS11Beta-180228
Compatibility: Compatible with python 3.6 which is used in RMS11Beta

### nrlib version 09.02.2018 for RMS11Beta
The directory nrlib-dist-RMS11Beta is the one to use for RMS11Beta
Compatibility: Compatible with python 3.6 which is used in RMS11Beta

### nrlib version pr 13.02.2018  for RMS10
The directory nrlib-dist-RMS10-optimalized is the one to use for RMS10.
Is updated to be more efficient. It generates an message which can be ignored:
   "RuntimeError: module compiled against API version 0xb but this version of numpy is 0xa"
This "error" message can be ignored.
Compatibility: Compatible with python 3.4 which is used in RMS10


##  Description
Python wrapper around Gaussian simulation methods for 1D, 2D and 3D simulation using the FFT based method.

Written by: Norsk Regnesentral for Equinor APS GUI project, but can be used for all in Equinor for internal use.

Contact person in Norsk Regnesentral: [Vegard Berg Kvernelv](mailto:Vegard.Kvernelv@nr.no) (2018)
Contact person in Equinor: [Oddvar Lia](mailto:olia@equinor.com)


This directory contains both source code and compiled version of nrlib,
a library for simulating gaussian fields in 1D, 2D and 3D using python 3.4 (RMS version 10 installation of python)

This code is for Equinor internal use and the development of the code is paid by the APS GUI project.
Norsk Regnesentral (contact person: Vegard Berg Kvernelv, 2018) has developed the code which is based on FFT
and can handle very large grids (The ambition is to handle up to 1000x1000x1000  grid size).
Check Docstring for usage but a brief summary follows:

How to use it in python scripts called up from RMS:
1. In RMS set python path to include: `/project/res/nrlib/nrlib-dist`
2. In python script: `import gaussianfft as grf`
3. Set variogram:
   `variogram = grf.variogram(variogramName, mainRange, perpRange,vertRange, azimuth, dip, power)`

   variogramName is one of:
              `exponential`
              `spherical`
              `gaussian`
              `general_exponential`  (this is the only one using the exponent called power in the variogram function)
              `matern32`
              `matern52`
              `matern72`
              `constant`
The ranges are given the same name as in IPL but corresponds to x,y,z directions.
Note that the simulation is a regular 3D grid and the coordinate system is right-handed. This means that input azimuth angle
should be  `(90 - azimut_used_in_rms)` for standard RMS grids which are left-handed.
So if you want to use this in RMS and load the result into a zone in a grid in RMS (e.g by using Roxar API) then be aware of this.

4. Simulation is done by:

   `gaussVector = grf.simulation(variogram, nx, dx, ny, dy, nz, dz)`

   The gauss field output is a 1D numpy array and by using

   `gaussResult = grf.reshape(gaussVector,(nx,ny,nz),order='F')`   one get a 3D numpy array

5. To check how large the extension of the internal simulation grid is (to avoid edge effects in the result from the FFT algorithm)
the grid is increased before it is simulated internally in the nrlib module. You can check this extension to see the actual grid size used.
This grid size is reported by using the function:

   `[nx_extended, ny_extended, nz_extended] = grf.simulation_size(variogram, nx, dx, ny, dy, nz, dz)`

    and depends very much on the relative size of the correlation lengths and the grid size (length, width, height)

6. To get the start seed that is used:
  `seed = grf.seed()`

7. To set a seed before calling any simulation:
  `grf.seed(seedValue)`

Note: the returned seed from `grf.seed()` is created automatically by the clock time. If you use multiprocessing, and run several processes in parallel
be sure to delay start of a new process by at least 1 second after the previous process to avoid that two different processes get the same start seed.

The return seed is the same regardless of how many times you call simulation since it is the start seed of the first call to simulation.
It must however not be called before the first call to simulation if you want the start seed to be automatically generated.
If you want to run with a predefined start seed, call `grf.seed(seedValue)` before the first call to simulation.



## Building
We use [`scikit-build-core`](https://scikit-build-core.readthedocs.io/en/latest/index.html) as the build tool, in order to use [`pyproject.toml`](https://pip.pypa.io/en/stable/reference/build-system/pyproject-toml/) to facilitate easier building while using [`cmake`](https://cmake.org) to build the C++ extension.

We also use [Boost.Python](https://www.boost.org/doc/libs/1_81_0/libs/python/doc/html/index.html) (version 1.76.0 for Python <=3.10 and 1.81.0 for newer versions).
While compiling Boost, a python interpreter needs to be set.
You may want to create a virtual environment before building `gaussianfft`.

```bash
python -m venv venv
source venv/bin/activate
```

For the time being, Windows is not supported due to difficulties making `gaussianfft` compile there (on a windows runner on GitHub Actions).
Contributions for making it compile reliably on Windows are welcome.

The rest of this section assumes you are working on a UNIX-like system.
It has been tested on macOS (Intel/Apple Silicon) and Linux (x86).

To build the distribution wheel(s), run
```bash
export PYTHON=<which python to use>  # Only useful when not running in a virtual environment 
make build
```
This will build the binary, and source distributions with the [`build`](https://github.com/pypa/build) package in a temporary / ephemeral directory.
There is no caching of build artifacts in this case.

If you need to build, and iterate on the extension module, you may want to execute

```bash
cmake -S . -B build -DPython3_EXECUTABLE=$(which python)
cmake --build build
```

## Contributing
Report bugs (description with reproducible steps + run environment) and feature requests are welcome.
