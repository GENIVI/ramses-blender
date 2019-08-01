#  Copyright (C) 2019 BMW AG, Daniel Werner Lima Souza de Almeida (dwlsalmeida@gmail.com)
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

import sys
import os
import bpy
import argparse

from ramses_export import debug_utils

class AdaptedArgParser(argparse.ArgumentParser):
    """ adapted argparser that prints help on error    """

    def error(self, message):
        print('error: %s\n' % message)
        self.print_help()
        sys.exit(1)

class ExporterTestBase:

    def __init__(self):
        parser = AdaptedArgParser()
        parser.add_argument("-w", "--working-dir", required=True, default=None, help='Working directory for this test')
        parser.add_argument("-p", "--platform", required=True, default=None, help="The platform to use for the renderer, such as 'X11-EGL-ES-3-0, WAYLAND-SHELL-EGL-ES-3-0, etc.")
        parser.add_argument("-a", "--addon-path", required=True, default=None, help='The install directory for the addon, e.g. "~/.config/blender/2.80/scripts/addons/ramses_export" or similar')
        index_of_double_dash = sys.argv.index('--')
        args_for_test_only = sys.argv[index_of_double_dash + 1:] if index_of_double_dash != -1 else []
        args = parser.parse_args(args_for_test_only)
        self.working_dir = args.working_dir
        self.platform = args.platform
        self.addon_path = args.addon_path

        debug_utils.setup_logging(os.path.join(self.working_dir, 'debug.txt'))
