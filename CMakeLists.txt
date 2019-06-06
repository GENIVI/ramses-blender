#  -------------------------------------------------------------------------
#  Copyright (C) 2019 BMW AG
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

cmake_minimum_required(VERSION 3.10)

set(project_name "ramses-export")
project(${project_name})
set(install_subdir ${project_name})

# TODO find a better way to handle this
set(CMAKE_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX}/${project_name})

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(ramses-python_INSTALL_PREFIX ${install_subdir})

# Important! This version has to be binary compatible with the one shipped
# with Blender!

unset(PYTHONINTERP_FOUND CACHE)
unset(PYTHON_EXECUTABLE CACHE)
set(PYBIND11_PYTHON_VERSION 3.7)
add_subdirectory(external/ramses-python)

# Installation
set(python_files
    __init__.py
    intermediary_representation.py
    exporter.py
)

# TODO add options in ramses to disable installation, or at least provide folder options
install(FILES ${python_files} DESTINATION .)

