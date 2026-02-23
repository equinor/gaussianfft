// Utility functions for nrlib C++ unit tests
#ifndef NRLIB_UNITTESTS_UTIL_HPP
#define NRLIB_UNITTESTS_UTIL_HPP

#include <boost/filesystem.hpp>
#include <cstdlib>

namespace {

/// Get the directory containing test data files
/// Looks for NRLIB_TEST_DATA environment variable, otherwise returns current directory
inline boost::filesystem::path GetTestDir() {
    const char* test_dir_env = std::getenv("NRLIB_TEST_DATA");
    if (test_dir_env) {
        return boost::filesystem::path(test_dir_env);
    }
    // Default to a testdata directory in the project root
    return boost::filesystem::path(__FILE__).parent_path().parent_path().parent_path().parent_path() / "testdata";
}

} // anonymous namespace

#endif // NRLIB_UNITTESTS_UTIL_HPP
