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

# TODO consider doing some more checks, e.g. addon folder has some addons
if(NOT BLENDER_ADDONS_PATH)
    message(FATAL_ERROR "Must set BLENDER_ADDONS_PATH variable!")
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

# TODO find a better way to control installation prefix for sub-projects
set(CMAKE_INSTALL_PREFIX ${BLENDER_ADDONS_PATH}/${project_name})
add_subdirectory(external/ramses-python)

# Installation
file(GLOB src_files
    *.py
)

file(GLOB test_files
    test/*.py
)

file(GLOB test_shader_library
    test/shader_library/*
)

install(FILES ${src_files} DESTINATION ${BLENDER_ADDONS_PATH}/${project_name}/)
install(FILES ${test_files} DESTINATION ${BLENDER_ADDONS_PATH}/${project_name}/test)
install(FILES ${test_shader_library} DESTINATION ${BLENDER_ADDONS_PATH}/${project_name}/test/shader_library)
install(FILES ${shader_files} DESTINATION ${BLENDER_ADDONS_PATH}/${project_name}/)

