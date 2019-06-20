#  -------------------------------------------------------------------------
#  Copyright (C) 2019 BMW AG
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
    parser.add_argument("-b", "--blender-binary", required=True, default=None, help='Path blender executable')
    parser.add_argument("-r", "--test-results-path", default=None, help='Path to store test results')

    args = parser.parse_args()
    if not os.path.exists(args.blender_binary):
        print(f'{args.blender_binary} is not a valid Blender executable!')
        return 1

    current_path = os.path.dirname(os.path.realpath(__file__))
    test_results = args.test_results_path if args.test_results_path else os.path.join(current_path, 'test_results')

    if os.path.exists(test_results):
        shutil.rmtree(test_results, ignore_errors=True)

    os.makedirs(test_results)
    
    tests = {
        'export_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/cube.png'),
                # TODO check if a more sophisticated check is needed
                'expected_output_files': 6,
            },
        'export_moved_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_moved.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/cube_moved.png'),
                'expected_output_files': 6,
            },
        'export_rotatedX_cube' :
            {
                'script'        : os.path.join(current_path, 'export_cube.py'),
                'test_scene'    : os.path.join(current_path, 'test_scenes/cube_rotatedX.blend'),
                'expected_image': os.path.join(current_path, 'expected_results/cube_rotatedX.png'),
                'expected_output_files': 6,
            }
    }

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
            ]

        p = subprocess.Popen(test_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=test_results)
        out, err = p.communicate()

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
        test_had_exceptions = ('Traceback' in err.decode('utf-8'))
        if test_had_exceptions:
            test_failed = True
            print('Test {} produced exceptions! Output from blender: {}'.format(test, err.decode('utf-8')))

        screenshot_image = os.path.join(test_results, test, 'screenshot.png')
        image_comparison = ImageComparison(screenshot_image, tests[test]['expected_image'])
        if not image_comparison.compare_images():
            test_failed = True
            print(f'Test {test} produced different screenshot than expected! Check {test_results} for results')

        if test_failed:
            failed_tests = failed_tests + [test]
            stdout_file = open(os.path.join(test_result_dir, 'stdout.txt'), 'w')
            stdout_file.write(out.decode('utf-8'))
            stderr_file = open(os.path.join(test_result_dir, 'stderr.txt'), 'w')
            stderr_file.write(err.decode('utf-8'))

    if failed_tests:
        print('Failed tests:')
        print("\n".join(failed_tests))
    else:
        print(f'All tests ran successfully! Check output at {test_results}')
    
    return len(failed_tests)

if __name__ == "__main__":
    sys.exit(main())
