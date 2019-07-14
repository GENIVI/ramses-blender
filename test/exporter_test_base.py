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
        index_of_double_dash = sys.argv.index('--')
        args_for_test_only = sys.argv[index_of_double_dash + 1:] if index_of_double_dash != -1 else []
        args = parser.parse_args(args_for_test_only)
        self.working_dir = args.working_dir

        debug_utils.setup_logging(os.path.join(self.working_dir, 'debug.txt'))
