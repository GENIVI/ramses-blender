import sys
import os
# TODO: Improve this, how is this not in there already?
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import unittest

import test_intermediary_representation

def run():
    suite_1 = unittest.defaultTestLoader.\
            loadTestsFromTestCase(test_intermediary_representation.TestVectorUnpack)
    suite_2 = unittest.defaultTestLoader.\
            loadTestsFromTestCase(test_intermediary_representation.TestFind)

    all_tests = unittest.TestSuite([suite_1,
                                    suite_2])

    success = unittest.TextTestRunner().run(all_tests).wasSuccessful()
    if not success:
        raise Exception('Unit tests failed')

run()
