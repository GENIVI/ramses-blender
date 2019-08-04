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
import subprocess

from ramses_export import debug_utils
from ramses_export.exporter import RamsesBlenderExporter

class AdaptedArgParser(argparse.ArgumentParser):
    """ adapted argparser that prints help on error    """

    def error(self, message):
        print('error: %s\n' % message)
        self.print_help()
        sys.exit(1)

class ExporterTestBase():
    """A base for test methods, for convenience. """
    # NOTE: due to the way tests are executed, 'make install' is needed every time this
    # class is changed

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

    def get_exportable_scenes_for_test(self,
                                       output_dir: str = '',
                                       addon_path: str = '',
                                       save: bool = True,
                                       num_scenes: int = 1,
                                       to_text: bool = True,
                                       open_viewer: bool = False,
                                       take_screenshot: bool = True,
                                       platform: str = ''):

        # Make configurable, but otherwise get them from CLI
        if not output_dir:
            output_dir = self.working_dir

        if not addon_path:
            addon_path = self.addon_path

        if not platform:
            platform = self.platform

        assert isinstance(num_scenes, int)
        assert num_scenes > 0

        if open_viewer or take_screenshot:
            # both are needed to pop up the scene viewer
            assert platform
            assert addon_path


        exporter = RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()
        exporter.build_from_extracted_representations()

        if len(exporter.get_exportable_scenes()) != num_scenes:
            raise AssertionError(f'Expected {num_scenes} scenes, found {len(exporter.get_exportable_scenes())}')

        exportable_scenes = exporter.get_exportable_scenes()

        for index, exportable_scene in enumerate(exportable_scenes):
            exportable_scene.set_output_dir(output_dir)

            if not exportable_scene.is_valid():
                validation_report = exportable_scene.get_validation_report()
                raise AssertionError(validation_report)

            if save:
                exportable_scene.save()

            if to_text:
                with open(os.path.join(self.working_dir, f'scene_{index}.txt'), 'w') as file:
                    file.write(exportable_scene.ramses_scene.toText())

            if open_viewer:
                program = f'ramses-scene-viewer-{platform}'
                cmd = [f'{addon_path}/bin/{program}',
                    '-s', f'{exportable_scene.output_path}/{exportable_scene.blender_scene.name}']

                viewer_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                viewer_process.wait()
                out, err = viewer_process.communicate()

                if err:
                    raise RuntimeError(err)

            if take_screenshot:
                screenshot_path = os.path.join(output_dir, f'screenshot.png')
                program = f'ramses-scene-viewer-{platform}'
                cmd = [f'{addon_path}/bin/{program}',
                    '-s', f'{exportable_scene.output_path}/{exportable_scene.blender_scene.name}',
                    '-x', screenshot_path,
                    '-xw', '800',
                    '-xh', '600']

                viewer_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = viewer_process.communicate()

                if viewer_process.returncode:
                    raise RuntimeError(viewer_process.returncode)
                if err:
                    raise RuntimeError(err)

        return exportable_scenes
