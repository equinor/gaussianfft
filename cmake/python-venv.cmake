set(VENV_INITIALIZED ON)
if (NOT EXISTS ${CMAKE_BINARY_DIR}/venv)
    message(STATUS "Creating a new venv in ${CMAKE_BINARY_DIR}/venv")
    find_package(Python3 ${Python3_VERSION} EXACT REQUIRED COMPONENTS Interpreter)
    execute_process(COMMAND ${Python3_EXECUTABLE} "-m" "venv" "venv"
            WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
            COMMAND_ERROR_IS_FATAL ANY
    )
    unset(${Python3_EXECUTABLE})
    set(VENV_INITIALIZED OFF)
endif ()
set(Python3_EXECUTABLE "${CMAKE_BINARY_DIR}/venv/bin/python")
find_package(Python3 REQUIRED COMPONENTS Interpreter)

if (NOT VENV_INITIALIZED)
    message(STATUS "Installing necessary dependencies in ${CMAKE_BINARY_DIR}/venv")

    file(COPY_FILE ${CMAKE_SOURCE_DIR}/pyproject.toml ${CMAKE_BINARY_DIR}/pyproject.toml)
    # Ensure pip ins up do date
    execute_process(
            COMMAND ${Python3_EXECUTABLE} -m pip install --upgrade pip
            COMMAND_ERROR_IS_FATAL ANY
    )
    # For very old version of pip, we may need to update it twice (e.g. Python 3.6)
    execute_process(
            COMMAND ${Python3_EXECUTABLE} -m pip install --upgrade pip
            COMMAND_ERROR_IS_FATAL ANY
    )
    execute_process(
            # Ensure toml / tomllib is installed
            COMMAND ${Python3_EXECUTABLE} -c "
try:
    # Newer versions of Python come with tomllib preinstalled
    import tomllib
except ImportError:
    try:
        import toml
    except ImportError:
        # Fall back on installing it
        import subprocess
        import sys
        subprocess.run(' '.join([
                sys.executable,
                '-m',
                'pip',
                'install',
                'toml',
            ]),
            shell=True,
            check=True,
        )
"
            COMMAND_ERROR_IS_FATAL ANY
    )
    execute_process(
            COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/bin/install-build-requirements.py
            COMMAND_ERROR_IS_FATAL ANY
    )
endif ()
