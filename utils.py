#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida
#                     dwlsalmeida at gmail dot com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

import os
from . import debug_utils
log = debug_utils.get_debug_logger()

def get_addon_path():
    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)
    return directory

class CustomParameters():
    """Extra parameters we might set that are not a part of the Blender scene itself"""
    def __init__(self):
        self.shader_dir = ''
