#  -------------------------------------------------------------------------
#  Copyright (C) 2019 BMW AG, Daniel Werner Lima Souza de Almeida
#                             dwlsalmeida@gmail.com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

import sys
import argparse
import os
import shutil
import subprocess

# pip install Pillow -> required for image tests
from PIL import Image
from PIL import ImageChops

class ImageComparison:

    def __init__(self, actual_image_path: str, expected_image_path: str):
        self.actual_image_path = actual_image_path
        self.actual_image = Image.open(actual_image_path)
        self.expected_image = Image.open(expected_image_path)


    def compare_images(self):
        actual = self.actual_image
        expected = self.expected_image

        if not self._check_image_size_equal():
            return False

        nrDifferentPixels = 0

        if actual != expected:
            imageDiff = ImageChops.difference(actual.convert("RGBA"), expected.convert("RGBA"))
            imageDiff.putalpha(255)
            root, ext = os.path.splitext(self.actual_image_path)
            imageDiff.save(root + "_DIFF" + ext)

            return False
        return True

    def _check_image_size_equal(self):
        if (self.actual_image.size[0] != self.expected_image.size[0]) or (self.actual_image.size[1] != self.expected_image.size[1]):
            return False
        return True

class AdaptedArgParser(argparse.ArgumentParser):
    """ adapted argparser that prints help on error    """

    def error(self, message):
        print('error: %s\n' % message)
        self.print_help()
        sys.exit(1)


def main():
    parser = AdaptedArgParser()
    # NOTE: to add arguments to tests first add them here, and them in 'test_args' and lastly
    # NOTE: in exporter_test_base.py
    parser.add_argument("-b", "--blender-binary", required=True, default=None, help='Path blender executable')
    parser.add_argument("-r", "--test-results-path", default=None, help='Path to store test results')
    parser.add_argument("-s", "--run-single-test", default=None, help='Run specific test')
    parser.add_argument("-p", "--platform", required=True, default=None, help="The platform to use for the renderer, such as 'X11-EGL-ES-3-0, WAYLAND-SHELL-EGL-ES-3-0, etc.")
    parser.add_argument("-a", "--addon-path", required=True, default=None, help='The install directory for the addon, e.g. "~/.config/blender/2.80/scripts/addons/ramses_export" or similar')
    parser.add_argument("-g", "--generate-expected-screenshots", required=False, default=False, action='store_true', help='Whether to copy the generated screenshots to "expected_results/"')

    args = parser.parse_args()
    if not os.path.exists(args.blender_binary):
        print(f'{args.blender_binary} is not a valid Blender executable!')
        return 1

    if not os.path.exists(args.addon_path):
        print(f'{args.addon_path} is not a valid path!')
        return 1
    current_path = os.path.dirname(os.path.realpath(__file__))
    test_results = args.test_results_path if args.test_results_path else os.path.join(current_path, 'test_results')

    if os.path.exists(test_results):
        shutil.rmtree(test_results, ignore_errors=True)

    os.makedirs(test_results)

    tests = {
        'unit_tests' :
            {
                'script'        : os.path.join(current_path, 'run_unit_tests.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube.blend'),
                'expected_image': '',
                # NOTE: need to save a scene to see it in the viewer
                'expected_output_files': 3, # debug.txt, Scene.ramses, Scene.ramres.
            },
        'export_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_cube.png'),
                # TODO check if a more sophisticated check is needed
                'expected_output_files': 5,
            },
        'export_cube_scaledX' :
            {
                'script'        : os.path.join(current_path, 'export_cube_scaledX.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_scaledX_2.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_cube_scaledX.png'),
                'expected_output_files': 5,
            },
        'export_cube_scaledY' :
            {
                'script'        : os.path.join(current_path, 'export_cube_scaledY.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_scaledY_2.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_cube_scaledY.png'),
                'expected_output_files': 5,
            },
        'export_cube_scaledZ' :
            {
                'script'        : os.path.join(current_path, 'export_cube_scaledZ.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_scaledZ_2.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_cube_scaledZ.png'),
                'expected_output_files': 5,
            },
        'export_cube_scaledXYZ' :
            {
                'script'        : os.path.join(current_path, 'export_cube_scaledXYZ.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_scaledXYZ_2.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_cube_scaledXYZ.png'),
                'expected_output_files': 5,
            },
        'export_moved_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_moved.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_moved_cube.png'),
                'expected_output_files': 5,
            },
        'export_rotatedX30_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube_rotated_X30.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_rotatedX30.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_rotatedX30_cube.png'),
                'expected_output_files': 5,
            },
        'export_rotatedY45_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube_rotated_Y45.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_rotatedY45.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_rotatedY45_cube.png'),
                'expected_output_files': 5,
            },
        'export_rotatedZ60_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube_rotated_Z60.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_rotatedZ60.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_rotatedZ60_cube.png'),
                'expected_output_files': 5,
            },
        'export_rotatedX30Y45Z60_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube_rotated_X30Y45Z60.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_rotated_X30Y45Z60.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_rotatedX30Y45Z60_cube.png'),
                'expected_output_files': 5,
            },
        'export_rotatedXYZ_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube_rotated_XYZ.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_rotated_XYZ.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_rotatedXYZ_cube.png'),
                'expected_output_files': 5,
            },
        'export_rotatedXZY_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube_rotated_XZY.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_rotated_XZY.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_rotatedXZY_cube.png'),
                'expected_output_files': 5,
            },
        'export_rotatedYZX_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube_rotated_YZX.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_rotated_YZX.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_rotatedYZX_cube.png'),
                'expected_output_files': 5,
            },
        'export_translated1X2Y3Z_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube_translated_1X2Y3Z.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_translated1X2Y3Z.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/export_translated1X2Y3Z_cube.png'),
                'expected_output_files': 5,
            },

    }

    if args.run_single_test:
        tests = {args.run_single_test: tests[args.run_single_test]}

    print('Found tests:')
    for test_name in tests:
        print(test_name)

    failed_tests = []
    for test in tests:
        test_result_dir = os.path.join(test_results, test)
        os.makedirs(test_result_dir)

        test_args = [
            args.blender_binary,
            tests[test]['test_scene'],                      # Input file for blender
            '-b',                                           # Run in batch mode (from command line)
            '-P', tests[test]['script'],                    # Execute script and close
            '--',                                           # Separator for script command line args
            '--working-dir', test_result_dir,               # Path to store results
            '--platform', args.platform,                    # Platform for the renderer
            '--addon-path', args.addon_path                 # Path to Blender's addons directory
            ]

        if args.generate_expected_screenshots:
            # NOTE: This is how boolean flags get handled.
            # NOTE: Should append if new boolean flags are added
            test_args.append('--generate-expected-screenshots') # Whether to copy screenshots into 'expected_results/'

        p = subprocess.Popen(test_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=test_results)
        out, err = p.communicate()

        if 'unrecognized arguments' in str(out):
            print(f"Test {test}: unrecognized arguments found, please check exporter_test_base.py")

        if test == 'unit_tests':
            print(f"UNIT TESTS OUTPUT: \n{err.decode('utf-8')}")

        test_failed = False
        if 0 != p.returncode:
            test_failed = True
            print(f'Test {test} returned code {p.returncode}!')

        output_files = os.listdir(test_result_dir)
        expected_output_files = tests[test]['expected_output_files']
        output_files_match_expectation = (len(output_files) == expected_output_files)
        if not output_files_match_expectation:
            test_failed = True
            print(f'Test {test} output mismatch! Expected {expected_output_files} files, but found instead:')
            print("\n".join(output_files) if output_files else 'No files')

        # No other way to check if the script threw an exception
        test_had_exceptions = ('Traceback' in err.decode('utf-8') or 'Error' in err.decode('utf-8'))
        if test_had_exceptions:
            test_failed = True
            print('Test {} produced exceptions! Output from blender: {}'.format(test, err.decode('utf-8')))

        if tests[test]['expected_image']:
            screenshot_image = os.path.join(test_results, test, 'screenshot.png')
            image_comparison = None
            try:
                image_comparison = ImageComparison(screenshot_image, tests[test]['expected_image'])
                if not image_comparison.compare_images():
                    test_failed = True
                    print(f'Test {test} produced different screenshot than expected! Check {test_results} for results')
            except FileNotFoundError as e:
                print(f'Test {test} failed, cannot compare screenshots: {str(e)}')
                test_failed = True


        if test_failed:
            failed_tests = failed_tests + [test]
            stdout_file = open(os.path.join(test_result_dir, 'stdout.txt'), 'w')
            stdout_file.write(out.decode('utf-8'))
            stderr_file = open(os.path.join(test_result_dir, 'stderr.txt'), 'w')
            stderr_file.write(err.decode('utf-8'))

    if failed_tests:
        print('Failed tests:')
        print("\n".join(failed_tests))
    elif args.generate_expected_screenshots:
        print(f'Tests executed successfully! Expected screenshots were updated and stored in the expected_results folder!')
    else:
        print(f'All tests ran successfully! Check output at {test_results}')

    return len(failed_tests)

if __name__ == "__main__":
    sys.exit(main())
