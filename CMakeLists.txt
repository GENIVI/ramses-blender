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

set(BLENDER_ADDONS_PATH "" CACHE PATH "Path to blender addons directory")
set(BLENDER_EXECUTABLE "" CACHE FILEPATH "Path to blender executable")

# TODO considering doing some more checks, e.g. that there is an executable called blender, and addon folder has some addons
if(NOT BLENDER_ADDONS_PATH OR NOT BLENDER_EXECUTABLE)
    message(FATAL_ERROR "Must set BLENDER_ADDONS_PATH and BLENDER_EXECUTABLE variables!")
endif()

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Needed in case of CMake-Cache presets from other dependencies which also require python
unset(PYTHONINTERP_FOUND CACHE)
unset(PYTHON_EXECUTABLE CACHE)
# Important! This version has to be binary compatible with the one shipped
# with Blender!
set(PYBIND11_PYTHON_VERSION 3.7)

# Temporary workaround to prevent ramses installation
# Fix ramses to be able to disable installation
set(CMAKE_INSTALL_PREFIX ${CMAKE_BINARY_DIR}/install)
add_subdirectory(external/ramses-python)

# Installation
file(GLOB src_files
    *.py
)

install(TARGETS RamsesPython LIBRARY DESTINATION ${BLENDER_ADDONS_PATH}/${project_name}/)
install(FILES ${src_files} DESTINATION ${BLENDER_ADDONS_PATH}/${project_name}/)

