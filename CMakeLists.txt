#  -------------------------------------------------------------------------
#  Copyright (C) 2019 BMW AG
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

cmake_minimum_required(VERSION 3.10)

set(project_name "ramses_export")
project(${project_name})
set(install_subdir ${project_name})

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

if(CMAKE_INSTALL_PREFIX STREQUAL "C:\\Program Files" OR CMAKE_INSTALL_PREFIX STREQUAL "/usr/local")
    message(FATAL_ERROR "CMAKE_INSTALL_PREFIX seems to have a default path. Please set it explicitly either to a blender add-on directory, or a custom path!")
endif()

# Needed in case of CMake-Cache presets from other dependencies which also require python
unset(PYTHONINTERP_FOUND CACHE)
unset(PYTHON_EXECUTABLE CACHE)
# Important! This version has to be binary compatible with the one shipped
# with Blender!
set(PYBIND11_PYTHON_VERSION 3.7)

set(CMAKE_INSTALL_PREFIX_FROM_USER ${CMAKE_INSTALL_PREFIX})
set(CMAKE_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX}/${install_subdir})
add_subdirectory(external/ramses-python)
set(CMAKE_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX_FROM_USER})

# Installation
file(GLOB python_files
    *.py
)

install(FILES ${python_files} DESTINATION ${CMAKE_INSTALL_PREFIX}/${install_subdir})

