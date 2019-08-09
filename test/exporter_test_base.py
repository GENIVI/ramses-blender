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
import shutil
import pathlib

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
        parser.add_argument("-g", "--generate-expected-screenshots", required=False, default=False, action='store_true', help='Whether to copy the generated screenshots to "expected_results/"')
        index_of_double_dash = sys.argv.index('--')
        args_for_test_only = sys.argv[index_of_double_dash + 1:] if index_of_double_dash != -1 else []
        args = parser.parse_args(args_for_test_only)
        self.working_dir = args.working_dir
        self.platform = args.platform.lower()
        self.addon_path = args.addon_path
        self.generate_expected_screenshots = args.generate_expected_screenshots

        debug_utils.setup_logging(os.path.join(self.working_dir, 'debug.txt'))

    def get_exportable_scenes_for_test(self,
                                       output_dir: str = '',
                                       addon_path: str = '',
                                       save: bool = True,
                                       num_scenes: int = 1,
                                       to_text: bool = True,
                                       open_viewer: bool = False,
                                       take_screenshot: bool = True,
                                       platform: str = '',
                                       generate_expected_screenshots: bool = False):

        # Make configurable, but otherwise get them from CLI
        if not output_dir:
            output_dir = self.working_dir

        if not addon_path:
            addon_path = self.addon_path

        if not platform:
            platform = self.platform

        if not generate_expected_screenshots:
            generate_expected_screenshots = self.generate_expected_screenshots

        assert isinstance(num_scenes, int)
        assert num_scenes > 0

        if open_viewer or take_screenshot:
            # both are needed to pop up the scene viewer
            assert platform
            assert platform.islower() # A common source of errors
            assert addon_path

        if generate_expected_screenshots:
            assert take_screenshot

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
                scene_full_path = pathlib.Path(exportable_scene.output_path).joinpath(f'{exportable_scene.blender_scene.name}.ramses')
                assert scene_full_path.exists(), f'Wrong scene path: {str(scene_full_path)}'

                program_args = f"-s {str(scene_full_path).replace('.ramses','')} -w {screenshot_resolution_x} -h {screenshot_resolution_y}"
                program = f'ramses-scene-viewer-{platform}'

                program_full_path = pathlib.Path(self.addon_path).joinpath('bin').joinpath(program)
                assert program_full_path.exists(), f'Wrong viewer path: {str(program_full_path)}'

                cmd = f'{str(program_full_path)} {program_args}'

                viewer_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                out, err = viewer_process.communicate()

                if err:
                    raise RuntimeError(err)

            if take_screenshot:
                screenshot_path = os.path.join(output_dir, f'screenshot.png')
                screenshot_resolution_x = exportable_scene.blender_scene.render.resolution_x
                screenshot_resolution_y = exportable_scene.blender_scene.render.resolution_y

                scene_full_path = pathlib.Path(exportable_scene.output_path).joinpath(f'{exportable_scene.blender_scene.name}.ramses')
                assert scene_full_path.exists(), f'Wrong scene path: {str(scene_full_path)}'

                program_args = f"-s {str(scene_full_path).replace('.ramses','')} -x {str(screenshot_path)} -xw {str(screenshot_resolution_x)} -xh {str(screenshot_resolution_y)}"
                program = f'ramses-scene-viewer-{platform}'

                program_full_path = pathlib.Path(self.addon_path).joinpath('bin').joinpath(program)
                assert program_full_path.exists(), f'Wrong viewer path: {str(program_full_path)}'

                cmd = f'{str(program_full_path)} {program_args}'

                viewer_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                out, err = viewer_process.communicate()

                if generate_expected_screenshots:
                    screenshot_current_path, _ = os.path.split(screenshot_path)
                    _, screenshot_current_dir = os.path.split(screenshot_current_path)
                    copied_screenshot_name = str(screenshot_current_dir)

                    save_path = os.path.join(screenshot_current_path, f'../../expected_results/{copied_screenshot_name}.png')
                    assert save_path
                    shutil.copyfile(screenshot_path, save_path)

                if viewer_process.returncode:
                    raise RuntimeError(viewer_process.returncode)
                if err:
                    raise RuntimeError(err)

                viewer_process.terminate()

        return exportable_scenes
