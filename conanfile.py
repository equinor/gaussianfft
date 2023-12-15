import sys
from pathlib import Path

import numpy as np
from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps


class gaussianfftRecipe(ConanFile):
    name = "gaussianfft"
    version = "1.1.1"
    package_type = "library"

    # Optional metadata
    license = "<Put the package license here>"
    author = "<Put your name here> <And your email here>"
    url = "<Package recipe repository url here, for issues about the package>"
    description = "<Description of gaussianfft package here>"
    topics = ("<Put some tag here>", "<here>", "<and here>")

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    # Sources are located in the same place as this recipe, copy them to the recipe
    exports_sources = "CMakeLists.txt", "src/*", "include/*"

    # Dependencies
    # 1.81.0 requires a newer version of Glibc++ than what's installed on CentOS 7 / manylinux2014
    # requires = ("boost/1.81.0", )

    def requirements(self):
        self.requires(
            "boost/1.81.0",
            options=dict(
                python_executable=sys.executable,
                shared=False,
                # By default, boost will not build python bindings, so we have to explicitly turn it on
                without_python=False,
                without_url=True,
                extra_b2_flags={
                    "python_debugging": 'off',
                    "link": "static",
                    "runtime_link": "static",
                },
            ),
        )

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        tc = CMakeToolchain(self)
        tc.variables.update({
            "Python3_NumPy_INCLUDE_DIRS": np.get_include(),
            "Python_ROOT_DIR": str(Path(sys.executable).parent.parent),
        })
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(
            variables={
                "Python3_NumPy_INCLUDE_DIRS": np.get_include(),
                "Python3_ROOT_DIR": str(Path(sys.executable).parent.parent),
            }
        )
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["gaussianfft"]




# if __name__ == '__main__':
#     import conans.conan
#     import conan.cli
#     conans.conan.main(["install", "conanfile.py", "--build='boost/1.81.0'"])
