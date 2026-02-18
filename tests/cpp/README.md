# NRLib C++ Unit Tests

Build and run NRLib C++ tests with Boost.Test.

## Requirements

- CMake 3.20+
- C++17 compiler
- `pkg-config`
- FFTW3 dev libraries (`fftw3`, `fftw3f`)
- Boost 1.74+ (`filesystem`, `unit_test_framework`)

## Run tests

From the project root:

```bash
./bin/run-cpp-tests.sh
```
## Current limitations

- Excluded modules: `flens`, `statistics`, `segy`, `well`, `backup`, `experimentation`.
- `Sim2dValuesSmall` in `gaussianfield_test.cpp` shows a large value mismatch and is intentionally disabled while the root cause is investigated.
