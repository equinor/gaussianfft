//
// Created by Sindre Nistad on 23/01/2024.
//

#ifndef BOOST_FILESYSTEM_HPP
#define BOOST_FILESYSTEM_HPP

#if defined(USE_BOOST) && __has_include(<boost/filesystem.hpp>)
// The helper methods that depend on boost::filesystem, is not used by the main
// gaussianfft library, but som of the debug functionallity use them
#include <boost/filesystem.hpp>
#define HAS_BOOST_FILESYSTEM 1
#endif

#endif //BOOST_FILESYSTEM_HPP
